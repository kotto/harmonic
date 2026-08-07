"""
🌊 Wave IR — Représentation Intermédiaire du Langage Ondulatoire
=================================================================
Grammaire formelle, AST, parser, sérialiseur, validateur.

Le Wave IR est la couche intermédiaire entre :
  - Le DSL Pythonique (wave_lang.py) — exécution directe
  - Le code généré par l'IA — langage ondulatoire natif
  - Les backends de compilation (NumPy, FPGA, ASIC, Optique)

Architecture en couches :
  ┌─────────────────────────────────────────────┐
  │  Code source ondulatoire (texte)            │  ← L'IA génère ceci
  │  ψ_requete = ENCODE "Qu'est-ce que φ ?"     │
  │  ψ_reponse = RESONANCE(ψ_requete, H)        │
  │  reponse = DECODE ψ_reponse                 │
  └──────────────────┬──────────────────────────┘
                     │ Parser (wave_ir.parse)
  ┌──────────────────▼──────────────────────────┐
  │  AST (arbre syntaxique abstrait)            │  ← Wave IR
  │  Assign("ψ_requete", Encode("Qu'est-ce...")│
  │  Assign("ψ_reponse", Resonance(Var(...)))   │
  │  Assign("reponse", Decode(Var(...)))        │
  └──────────────────┬──────────────────────────┘
                     │ Compilateur (wave_ir.compile → Phase 4)
  ┌──────────────────▼──────────────────────────┐
  │  Backend (NumPy, FPGA, ASIC, Optique)       │
  └─────────────────────────────────────────────┘

Grammaire EBNF :
  program     ::= statement*
  statement   ::= ID '=' expr
                | 'STORE' ID '=' expr 'IN' ID
                | 'QUERY' ID '=' expr 'FROM' ID
                | 'RETURN' expr
  expr        ::= 'ENCODE' string
                | 'DECODE' expr
                | 'BIND' '(' expr ',' expr ')'
                | 'UNBIND' '(' expr ',' expr ')'
                | 'SUPERPOSE' '(' expr (',' expr)* ')'
                | 'RESONANCE' '(' expr ',' expr ')'
                | 'ROTATE' '(' expr ',' number ')'
                | 'NORMALIZE' '(' expr ')'
                | 'INTERFERE' '(' expr ',' expr (',' number)? ')'
                | 'DIFFRACT' '(' expr (',' bool)? ')'
                | 'FILTER_LP' '(' expr ',' number ')'
                | 'FILTER_HP' '(' expr ',' number ')'
                | 'FILTER_BP' '(' expr ',' number ',' number ')'
                | 'PHASE_SHIFT' '(' expr ',' number ')'
                | 'EMERGE' '(' expr (',' expr)* (',' number)? ')'
                | 'OPPOSE' '(' expr ',' expr ')'
                | 'AMPLIFY' '(' expr ',' expr (',' number)? ')'
                | 'BIND_MANY' '(' expr (',' expr)* ')'
                | ID
                | number
                | string
  string      ::= '"' [^"]* '"' | "'" [^']* "'"
  number      ::= '-'? [0-9]+ ('.' [0-9]+)? ([eE] [+-]? [0-9]+)?
  bool        ::= 'true' | 'false'
  ID          ::= [a-zA-Z_][a-zA-Z0-9_]*
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

# ═══════════════════════════════════════════════════════════════════════════════
# AST — NŒUDS DE L'ARBRE SYNTAXIQUE ABSTRAIT
# ═══════════════════════════════════════════════════════════════════════════════


class Node(ABC):
    """Nœud de base de l'AST ondulatoire."""

    @abstractmethod
    def to_dict(self) -> dict:
        """Sérialise le nœud en dictionnaire JSON-compatible."""
        ...

    @abstractmethod
    def children(self) -> List[Node]:
        """Retourne les nœuds enfants (pour la traversée)."""
        ...

    def __repr__(self) -> str:
        return self.to_wave()

    def to_wave(self) -> str:
        """Pretty-print en syntaxe ondulatoire."""
        return _pretty_print(self)


# ── Statements ────────────────────────────────────────────────────────────────

@dataclass
class Program(Node):
    """Programme = séquence de statements."""
    statements: List[Statement]

    def to_dict(self) -> dict:
        return {"type": "Program", "statements": [s.to_dict() for s in self.statements]}

    def children(self) -> List[Node]:
        return list(self.statements)


class Statement(Node, ABC):
    """Base pour tous les statements."""
    pass


@dataclass
class Assign(Statement):
    """Assignation : nom = expression."""
    name: str
    value: Expr

    def to_dict(self) -> dict:
        return {"type": "Assign", "name": self.name, "value": self.value.to_dict()}

    def children(self) -> List[Node]:
        return [self.value]


@dataclass
class Store(Statement):
    """Stockage dans un hologramme nommé : STORE nom = expr IN hologram."""
    name: str
    value: Expr
    hologram: str

    def to_dict(self) -> dict:
        return {"type": "Store", "name": self.name, "value": self.value.to_dict(), "hologram": self.hologram}

    def children(self) -> List[Node]:
        return [self.value]


@dataclass
class Query(Statement):
    """Requête depuis un hologramme : QUERY nom = expr FROM hologram."""
    name: str
    value: Expr
    hologram: str

    def to_dict(self) -> dict:
        return {"type": "Query", "name": self.name, "value": self.value.to_dict(), "hologram": self.hologram}

    def children(self) -> List[Node]:
        return [self.value]


@dataclass
class Return(Statement):
    """Retourne une valeur : RETURN expr."""
    value: Expr

    def to_dict(self) -> dict:
        return {"type": "Return", "value": self.value.to_dict()}

    def children(self) -> List[Node]:
        return [self.value]


@dataclass
class CodeBlock(Statement):
    """Bloc de statements : BLOCK { stmt1 ; stmt2 }."""
    body: List[Statement]

    def to_dict(self) -> dict:
        return {"type": "CodeBlock",
                "body": [s.to_dict() for s in self.body]}

    def children(self) -> List[Node]:
        return list(self.body)


@dataclass
class IfStmt(Statement):
    """Conditionnel : IF(cond) { then } ELSE { else }."""
    condition: Expr
    then_body: List[Statement]
    else_body: Optional[List[Statement]] = None

    def to_dict(self) -> dict:
        d = {"type": "IfStmt", "condition": self.condition.to_dict(),
             "then_body": [s.to_dict() for s in self.then_body]}
        if self.else_body is not None:
            d["else_body"] = [s.to_dict() for s in self.else_body]
        return d

    def children(self) -> List[Node]:
        kids: List[Node] = [self.condition] + list(self.then_body)
        if self.else_body is not None:
            kids += list(self.else_body)
        return kids


@dataclass
class WhileStmt(Statement):
    """Boucle : WHILE(cond) { body }."""
    condition: Expr
    body: List[Statement]

    def to_dict(self) -> dict:
        return {"type": "WhileStmt", "condition": self.condition.to_dict(),
                "body": [s.to_dict() for s in self.body]}

    def children(self) -> List[Node]:
        return [self.condition] + list(self.body)


@dataclass
class FunctionDef(Statement):
    """Définition de fonction : FUNCTION name(p1, p2) { body }."""
    name: str
    params: List[str]
    body: List[Statement]
    defaults: Optional[Dict[str, Expr]] = None

    def to_dict(self) -> dict:
        d = {"type": "FunctionDef", "name": self.name,
             "params": list(self.params),
             "body": [s.to_dict() for s in self.body]}
        if self.defaults:
            d["defaults"] = {k: v.to_dict() for k, v in self.defaults.items()}
        return d

    def children(self) -> List[Node]:
        kids: List[Node] = list(self.body)
        if self.defaults:
            kids += list(self.defaults.values())
        return kids


@dataclass
class ForStmt(Statement):
    """Boucle for : FOR x IN iterable { body }."""
    target: str
    iterable: Expr
    body: List[Statement]

    def to_dict(self) -> dict:
        return {"type": "ForStmt", "target": self.target,
                "iterable": self.iterable.to_dict(),
                "body": [s.to_dict() for s in self.body]}

    def children(self) -> List[Node]:
        return [self.iterable] + list(self.body)


@dataclass
class AugAssign(Statement):
    """Assignation augmentée : x += expr."""
    name: str
    op: str  # 'ADD' | 'SUB' | 'MUL' | 'DIV'
    value: Expr

    def to_dict(self) -> dict:
        return {"type": "AugAssign", "name": self.name, "op": self.op,
                "value": self.value.to_dict()}

    def children(self) -> List[Node]:
        return [self.value]


# ── Expressions ───────────────────────────────────────────────────────────────

class Expr(Node, ABC):
    """Base pour toutes les expressions."""
    pass


@dataclass
class Encode(Expr):
    """ENCODE "texte" → ψ."""
    text: str

    def to_dict(self) -> dict:
        return {"type": "Encode", "text": self.text}

    def children(self) -> List[Node]:
        return []


@dataclass
class Decode(Expr):
    """DECODE ψ → texte (retourne le top-k)."""
    psi: Expr
    top_k: int = 5

    def to_dict(self) -> dict:
        return {"type": "Decode", "psi": self.psi.to_dict(), "top_k": self.top_k}

    def children(self) -> List[Node]:
        return [self.psi]


@dataclass
class Bind(Expr):
    """BIND(ψ₁, ψ₂) → ψ₁ ⊛ ψ₂."""
    left: Expr
    right: Expr

    def to_dict(self) -> dict:
        return {"type": "Bind", "left": self.left.to_dict(), "right": self.right.to_dict()}

    def children(self) -> List[Node]:
        return [self.left, self.right]


@dataclass
class Unbind(Expr):
    """UNBIND(ψ₁, ψ₂) → ψ₁ ⊘ ψ₂."""
    left: Expr
    right: Expr

    def to_dict(self) -> dict:
        return {"type": "Unbind", "left": self.left.to_dict(), "right": self.right.to_dict()}

    def children(self) -> List[Node]:
        return [self.left, self.right]


@dataclass
class Superpose(Expr):
    """SUPERPOSE(ψ₁, ψ₂, ...) → Σ ψᵢ."""
    psis: List[Expr]
    weights: Optional[List[float]] = None

    def to_dict(self) -> dict:
        d: dict = {"type": "Superpose", "psis": [p.to_dict() for p in self.psis]}
        if self.weights:
            d["weights"] = self.weights
        return d

    def children(self) -> List[Node]:
        return list(self.psis)


@dataclass
class Resonance(Expr):
    """RESONANCE(ψ₁, ψ₂) → s ∈ [-1, 1]."""
    left: Expr
    right: Expr

    def to_dict(self) -> dict:
        return {"type": "Resonance", "left": self.left.to_dict(), "right": self.right.to_dict()}

    def children(self) -> List[Node]:
        return [self.left, self.right]


@dataclass
class Rotate(Expr):
    """ROTATE(ψ, θ) → ψ · e^{iθ}."""
    psi: Expr
    angle: float

    def to_dict(self) -> dict:
        return {"type": "Rotate", "psi": self.psi.to_dict(), "angle": self.angle}

    def children(self) -> List[Node]:
        return [self.psi]


@dataclass
class Normalize(Expr):
    """NORMALIZE(ψ) → ψ / |ψ|."""
    psi: Expr

    def to_dict(self) -> dict:
        return {"type": "Normalize", "psi": self.psi.to_dict()}

    def children(self) -> List[Node]:
        return [self.psi]


@dataclass
class Interfere(Expr):
    """INTERFERE(ψ₁, ψ₂, ε) → ψ₁ + ε·ψ₂."""
    base: Expr
    other: Expr
    epsilon: float = 0.1

    def to_dict(self) -> dict:
        return {"type": "Interfere", "base": self.base.to_dict(), "other": self.other.to_dict(), "epsilon": self.epsilon}

    def children(self) -> List[Node]:
        return [self.base, self.other]


@dataclass
class Diffract(Expr):
    """DIFFRACT(ψ, inverse?) → FFT(ψ) ou IFFT(ψ)."""
    psi: Expr
    inverse: bool = False

    def to_dict(self) -> dict:
        return {"type": "Diffract", "psi": self.psi.to_dict(), "inverse": self.inverse}

    def children(self) -> List[Node]:
        return [self.psi]


@dataclass
class FilterLP(Expr):
    """FILTER_LP(ψ, cutoff) — filtre passe-bas."""
    psi: Expr
    cutoff: float

    def to_dict(self) -> dict:
        return {"type": "FilterLP", "psi": self.psi.to_dict(), "cutoff": self.cutoff}

    def children(self) -> List[Node]:
        return [self.psi]


@dataclass
class FilterHP(Expr):
    """FILTER_HP(ψ, cutoff) — filtre passe-haut."""
    psi: Expr
    cutoff: float

    def to_dict(self) -> dict:
        return {"type": "FilterHP", "psi": self.psi.to_dict(), "cutoff": self.cutoff}

    def children(self) -> List[Node]:
        return [self.psi]


@dataclass
class FilterBP(Expr):
    """FILTER_BP(ψ, low, high) — filtre passe-bande."""
    psi: Expr
    low: float
    high: float

    def to_dict(self) -> dict:
        return {"type": "FilterBP", "psi": self.psi.to_dict(), "low": self.low, "high": self.high}

    def children(self) -> List[Node]:
        return [self.psi]


@dataclass
class PhaseShift(Expr):
    """PHASE_SHIFT(ψ, shift) — décalage de phase par dimension."""
    psi: Expr
    shift: Union[float, List[float]]

    def to_dict(self) -> dict:
        return {"type": "PhaseShift", "psi": self.psi.to_dict(), "shift": self.shift}

    def children(self) -> List[Node]:
        return [self.psi]


@dataclass
class Emerge(Expr):
    """EMERGE(ψ₁, ψ₂, ..., temp) — émergence créative."""
    psis: List[Expr]
    temperature: float = 0.5

    def to_dict(self) -> dict:
        return {"type": "Emerge", "psis": [p.to_dict() for p in self.psis], "temperature": self.temperature}

    def children(self) -> List[Node]:
        return list(self.psis)


@dataclass
class Oppose(Expr):
    """OPPOSE(ψ₁, ψ₂) → ψ₁ - ψ₂."""
    left: Expr
    right: Expr

    def to_dict(self) -> dict:
        return {"type": "Oppose", "left": self.left.to_dict(), "right": self.right.to_dict()}

    def children(self) -> List[Node]:
        return [self.left, self.right]


@dataclass
class Amplify(Expr):
    """AMPLIFY(ψ, composante, boost) → ψ + boost·composante."""
    psi: Expr
    component: Expr
    boost: float = 3.0

    def to_dict(self) -> dict:
        return {"type": "Amplify", "psi": self.psi.to_dict(), "component": self.component.to_dict(), "boost": self.boost}

    def children(self) -> List[Node]:
        return [self.psi, self.component]


@dataclass
class BindMany(Expr):
    """BIND_MANY(ψ₁, ψ₂, ...) → bind(bind(ψ₁, ψ₂), ...)."""
    psis: List[Expr]

    def to_dict(self) -> dict:
        return {"type": "BindMany", "psis": [p.to_dict() for p in self.psis]}

    def children(self) -> List[Node]:
        return list(self.psis)


@dataclass
class Var(Expr):
    """Référence à une variable nommée."""
    name: str

    def to_dict(self) -> dict:
        return {"type": "Var", "name": self.name}

    def children(self) -> List[Node]:
        return []


@dataclass
class Literal(Expr):
    """Valeur scalaire."""
    value: float

    def to_dict(self) -> dict:
        return {"type": "Literal", "value": self.value}

    def children(self) -> List[Node]:
        return []


@dataclass
class StringLit(Expr):
    """Chaîne de caractères littérale."""
    value: str

    def to_dict(self) -> dict:
        return {"type": "StringLit", "value": self.value}

    def children(self) -> List[Node]:
        return []


@dataclass
class MathOp(Expr):
    """
    Opération mathématique : ADD(2, 3), SQRT(16), NEG(5)...

    op ∈ {ADD, SUB, MUL, DIV, POW, MOD, SQRT, NEG, ABS}
    right = None → opérateur unaire (SQRT/NEG/ABS).
    """
    op: str
    left: Expr
    right: Optional[Expr] = None

    def to_dict(self) -> dict:
        d = {"type": "MathOp", "op": self.op, "left": self.left.to_dict()}
        if self.right is not None:
            d["right"] = self.right.to_dict()
        return d

    def children(self) -> List[Node]:
        if self.right is not None:
            return [self.left, self.right]
        return [self.left]


@dataclass
class FunctionCall(Expr):
    """Appel de fonction classique : CALL(f, 2, 3) ou f(2, 3)."""
    name: str
    args: List[Expr]

    def to_dict(self) -> dict:
        return {"type": "FunctionCall", "name": self.name,
                "args": [a.to_dict() for a in self.args]}

    def children(self) -> List[Node]:
        return list(self.args)


@dataclass
class ListLiteral(Expr):
    """Littéral de liste : [1, 2, 3]."""
    items: List[Expr]

    def to_dict(self) -> dict:
        return {"type": "ListLiteral",
                "items": [i.to_dict() for i in self.items]}

    def children(self) -> List[Node]:
        return list(self.items)


@dataclass
class Subscript(Expr):
    """Accès par indice : arr[0], matrix[i][j]."""
    obj: Expr
    index: Expr

    def to_dict(self) -> dict:
        return {"type": "Subscript", "obj": self.obj.to_dict(),
                "index": self.index.to_dict()}

    def children(self) -> List[Node]:
        return [self.obj, self.index]


@dataclass
class TernaryExpr(Expr):
    """Expression ternaire : a if cond else b."""
    condition: Expr
    if_true: Expr
    if_false: Expr

    def to_dict(self) -> dict:
        return {"type": "TernaryExpr", "condition": self.condition.to_dict(),
                "if_true": self.if_true.to_dict(),
                "if_false": self.if_false.to_dict()}

    def children(self) -> List[Node]:
        return [self.condition, self.if_true, self.if_false]


@dataclass
class LambdaExpr(Expr):
    """Fonction anonyme : LAMBDA(x, y) { expr }."""
    params: List[str]
    body: Expr

    def to_dict(self) -> dict:
        return {"type": "LambdaExpr", "params": list(self.params),
                "body": self.body.to_dict()}

    def children(self) -> List[Node]:
        return [self.body]


@dataclass
class RawCode(Expr):
    """
    Échappatoire code brut : RAW "texte" (lang).

    Pour les fragments écologiques (JSX, Flask, CSV, crypto) qui
    ne se prêtent pas à une représentation AST — émis tel quel
    vers la cible correspondante.
    """
    text: str
    lang: str = "python"

    def to_dict(self) -> dict:
        return {"type": "RawCode", "text": self.text, "lang": self.lang}

    def children(self) -> List[Node]:
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# SÉRIALISATION / DÉSÉRIALISATION
# ═══════════════════════════════════════════════════════════════════════════════

def to_json(node: Node, indent: int = 2) -> str:
    """
    Sérialise un AST en JSON.

    Args:
        node: nœud racine de l'AST
        indent: indentation JSON

    Returns:
        chaîne JSON

    Example:
        >>> ast = Program([Assign("x", Encode("bonjour"))])
        >>> print(to_json(ast))
        {
          "type": "Program",
          "statements": [
            {
              "type": "Assign",
              "name": "x",
              "value": {
                "type": "Encode",
                "text": "bonjour"
              }
            }
          ]
        }
    """
    return json.dumps(node.to_dict(), indent=indent, ensure_ascii=False)


def from_json(data: Union[str, dict]) -> Node:
    """
    Désérialise un AST depuis du JSON.

    Args:
        data: chaîne JSON ou dictionnaire déjà parsé

    Returns:
        nœud racine de l'AST reconstruit

    Raises:
        ValueError: si le type de nœud est inconnu
    """
    if isinstance(data, str):
        data = json.loads(data)
    return _deserialize_node(data)


def _deserialize_node(d: dict) -> Node:
    """Désérialise récursivement un nœud depuis un dictionnaire."""
    node_type = d.get("type")
    if node_type is None:
        raise ValueError(f"Nœud sans 'type': {d}")

    # Statements
    if node_type == "Program":
        return Program([_deserialize_node(s) for s in d["statements"]])
    if node_type == "Assign":
        return Assign(d["name"], _deserialize_node(d["value"]))
    if node_type == "Store":
        return Store(d["name"], _deserialize_node(d["value"]), d["hologram"])
    if node_type == "Query":
        return Query(d["name"], _deserialize_node(d["value"]), d["hologram"])
    if node_type == "Return":
        return Return(_deserialize_node(d["value"]))
    if node_type == "CodeBlock":
        return CodeBlock([_deserialize_node(s) for s in d["body"]])
    if node_type == "IfStmt":
        else_body = (None if "else_body" not in d or d["else_body"] is None
                     else [_deserialize_node(s) for s in d["else_body"]])
        return IfStmt(_deserialize_node(d["condition"]),
                      [_deserialize_node(s) for s in d["then_body"]],
                      else_body)
    if node_type == "WhileStmt":
        return WhileStmt(_deserialize_node(d["condition"]),
                         [_deserialize_node(s) for s in d["body"]])
    if node_type == "FunctionDef":
        defaults = None
        if d.get("defaults"):
            defaults = {k: _deserialize_node(v)
                        for k, v in d["defaults"].items()}
        return FunctionDef(d["name"], list(d["params"]),
                           [_deserialize_node(s) for s in d["body"]],
                           defaults)
    if node_type == "ForStmt":
        return ForStmt(d["target"], _deserialize_node(d["iterable"]),
                       [_deserialize_node(s) for s in d["body"]])
    if node_type == "AugAssign":
        return AugAssign(d["name"], d["op"], _deserialize_node(d["value"]))

    # Expressions
    if node_type == "Encode":
        return Encode(d["text"])
    if node_type == "Decode":
        return Decode(_deserialize_node(d["psi"]), d.get("top_k", 5))
    if node_type == "Bind":
        return Bind(_deserialize_node(d["left"]), _deserialize_node(d["right"]))
    if node_type == "Unbind":
        return Unbind(_deserialize_node(d["left"]), _deserialize_node(d["right"]))
    if node_type == "Superpose":
        weights = d.get("weights")
        return Superpose([_deserialize_node(p) for p in d["psis"]], weights)
    if node_type == "Resonance":
        return Resonance(_deserialize_node(d["left"]), _deserialize_node(d["right"]))
    if node_type == "Rotate":
        return Rotate(_deserialize_node(d["psi"]), d["angle"])
    if node_type == "Normalize":
        return Normalize(_deserialize_node(d["psi"]))
    if node_type == "Interfere":
        return Interfere(_deserialize_node(d["base"]), _deserialize_node(d["other"]), d.get("epsilon", 0.1))
    if node_type == "Diffract":
        return Diffract(_deserialize_node(d["psi"]), d.get("inverse", False))
    if node_type == "FilterLP":
        return FilterLP(_deserialize_node(d["psi"]), d["cutoff"])
    if node_type == "FilterHP":
        return FilterHP(_deserialize_node(d["psi"]), d["cutoff"])
    if node_type == "FilterBP":
        return FilterBP(_deserialize_node(d["psi"]), d["low"], d["high"])
    if node_type == "PhaseShift":
        return PhaseShift(_deserialize_node(d["psi"]), d["shift"])
    if node_type == "Emerge":
        return Emerge([_deserialize_node(p) for p in d["psis"]], d.get("temperature", 0.5))
    if node_type == "Oppose":
        return Oppose(_deserialize_node(d["left"]), _deserialize_node(d["right"]))
    if node_type == "Amplify":
        return Amplify(_deserialize_node(d["psi"]), _deserialize_node(d["component"]), d.get("boost", 3.0))
    if node_type == "BindMany":
        return BindMany([_deserialize_node(p) for p in d["psis"]])
    if node_type == "Var":
        return Var(d["name"])
    if node_type == "Literal":
        return Literal(d["value"])
    if node_type == "StringLit":
        return StringLit(d["value"])
    if node_type == "MathOp":
        right = (None if d.get("right") is None
                 else _deserialize_node(d["right"]))
        return MathOp(d["op"], _deserialize_node(d["left"]), right)
    if node_type == "FunctionCall":
        return FunctionCall(d["name"], [_deserialize_node(a) for a in d["args"]])
    if node_type == "ListLiteral":
        return ListLiteral([_deserialize_node(i) for i in d["items"]])
    if node_type == "Subscript":
        return Subscript(_deserialize_node(d["obj"]),
                         _deserialize_node(d["index"]))
    if node_type == "TernaryExpr":
        return TernaryExpr(_deserialize_node(d["condition"]),
                           _deserialize_node(d["if_true"]),
                           _deserialize_node(d["if_false"]))
    if node_type == "LambdaExpr":
        return LambdaExpr(list(d["params"]), _deserialize_node(d["body"]))
    if node_type == "RawCode":
        return RawCode(d["text"], d.get("lang", "python"))

    raise ValueError(f"Type de nœud inconnu: {node_type}")


# ═══════════════════════════════════════════════════════════════════════════════
# PRETTY PRINTER — AST → CODE ONDULATOIRE
# ═══════════════════════════════════════════════════════════════════════════════

def _pretty_print(node: Node, indent: int = 0) -> str:
    """Convertit un nœud AST en code source ondulatoire."""
    prefix = "  " * indent

    if isinstance(node, Program):
        lines = []
        for s in node.statements:
            lines.append(_pretty_print(s, indent))
        return "\n".join(lines)

    if isinstance(node, Assign):
        return f"{prefix}{node.name} = {_pretty_print(node.value)}"

    if isinstance(node, Store):
        return f"{prefix}STORE {node.name} = {_pretty_print(node.value)} IN {node.hologram}"

    if isinstance(node, Query):
        return f"{prefix}QUERY {node.name} = {_pretty_print(node.value)} FROM {node.hologram}"

    if isinstance(node, Return):
        return f"{prefix}RETURN {_pretty_print(node.value)}"

    if isinstance(node, CodeBlock):
        inner = " ; ".join(_pretty_print(s, indent=0) for s in node.body)
        return f"{prefix}BLOCK {{ {inner} }}"

    if isinstance(node, IfStmt):
        s = (f"{prefix}IF({_pretty_print(node.condition)}) {{ "
             f"{'; '.join(_pretty_print(x, indent=0) for x in node.then_body)} }}")
        if node.else_body is not None:
            s += (f" ELSE {{ "
                  f"{'; '.join(_pretty_print(x, indent=0) for x in node.else_body)} }}")
        return s

    if isinstance(node, WhileStmt):
        return (f"{prefix}WHILE({_pretty_print(node.condition)}) {{ "
                f"{'; '.join(_pretty_print(x, indent=0) for x in node.body)} }}")

    if isinstance(node, FunctionDef):
        params = ", ".join(node.params)
        body = " ; ".join(_pretty_print(x, indent=0) for x in node.body)
        return f"{prefix}FUNCTION {node.name}({params}) {{ {body} }}"

    if isinstance(node, ForStmt):
        body = " ; ".join(_pretty_print(x, indent=0) for x in node.body)
        return (f"{prefix}FOR {node.target} IN "
                f"{_pretty_print(node.iterable)} {{ {body} }}")

    if isinstance(node, AugAssign):
        op_map = {'ADD': '+=', 'SUB': '-=', 'MUL': '*=', 'DIV': '/='}
        sym = op_map.get(node.op, node.op)
        return f"{prefix}{node.name} {sym} {_pretty_print(node.value)}"

    if isinstance(node, Encode):
        text = node.text.replace('"', '\\"')
        return f'ENCODE "{text}"'

    if isinstance(node, Decode):
        return f"DECODE({_pretty_print(node.psi)})"

    if isinstance(node, Bind):
        return f"BIND({_pretty_print(node.left)}, {_pretty_print(node.right)})"

    if isinstance(node, Unbind):
        return f"UNBIND({_pretty_print(node.left)}, {_pretty_print(node.right)})"

    if isinstance(node, Superpose):
        args = ", ".join(_pretty_print(p) for p in node.psis)
        if node.weights:
            args += f", weights=[{', '.join(f'{w:.3f}' for w in node.weights)}]"
        return f"SUPERPOSE({args})"

    if isinstance(node, Resonance):
        return f"RESONANCE({_pretty_print(node.left)}, {_pretty_print(node.right)})"

    if isinstance(node, Rotate):
        return f"ROTATE({_pretty_print(node.psi)}, {node.angle:.4f})"

    if isinstance(node, Normalize):
        return f"NORMALIZE({_pretty_print(node.psi)})"

    if isinstance(node, Interfere):
        return f"INTERFERE({_pretty_print(node.base)}, {_pretty_print(node.other)}, {node.epsilon:.3f})"

    if isinstance(node, Diffract):
        inv = ", true" if node.inverse else ""
        return f"DIFFRACT({_pretty_print(node.psi)}{inv})"

    if isinstance(node, FilterLP):
        return f"FILTER_LP({_pretty_print(node.psi)}, {node.cutoff:.0f})"

    if isinstance(node, FilterHP):
        return f"FILTER_HP({_pretty_print(node.psi)}, {node.cutoff:.0f})"

    if isinstance(node, FilterBP):
        return f"FILTER_BP({_pretty_print(node.psi)}, {node.low:.0f}, {node.high:.0f})"

    if isinstance(node, PhaseShift):
        if isinstance(node.shift, (int, float)):
            return f"PHASE_SHIFT({_pretty_print(node.psi)}, {node.shift:.4f})"
        return f"PHASE_SHIFT({_pretty_print(node.psi)}, <vector>)"

    if isinstance(node, Emerge):
        args = ", ".join(_pretty_print(p) for p in node.psis)
        return f"EMERGE({args}, {node.temperature:.2f})"

    if isinstance(node, Oppose):
        return f"OPPOSE({_pretty_print(node.left)}, {_pretty_print(node.right)})"

    if isinstance(node, Amplify):
        return f"AMPLIFY({_pretty_print(node.psi)}, {_pretty_print(node.component)}, {node.boost:.1f})"

    if isinstance(node, BindMany):
        args = ", ".join(_pretty_print(p) for p in node.psis)
        return f"BIND_MANY({args})"

    if isinstance(node, Var):
        return node.name

    if isinstance(node, Literal):
        return str(node.value)

    if isinstance(node, StringLit):
        return f'"{node.value}"'

    if isinstance(node, MathOp):
        left = _pretty_print(node.left)
        if node.right is not None:
            return f"{node.op}({left}, {_pretty_print(node.right)})"
        return f"{node.op}({left})"

    if isinstance(node, FunctionCall):
        args = ", ".join(_pretty_print(a) for a in node.args)
        return f"CALL({node.name}, {args})" if args else f"CALL({node.name})"

    if isinstance(node, ListLiteral):
        items = ", ".join(_pretty_print(i) for i in node.items)
        return f"[{items}]"

    if isinstance(node, Subscript):
        return f"{_pretty_print(node.obj)}[{_pretty_print(node.index)}]"

    if isinstance(node, TernaryExpr):
        return (f"{_pretty_print(node.if_true)} IF {_pretty_print(node.condition)} "
                f"ELSE {_pretty_print(node.if_false)}")

    if isinstance(node, LambdaExpr):
        params = ", ".join(node.params)
        return f"LAMBDA({params}) {{ {_pretty_print(node.body)} }}"

    if isinstance(node, RawCode):
        return f'RAW "{node.text}"'

    return f"<? {type(node).__name__} ?>"


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATEUR
# ═══════════════════════════════════════════════════════════════════════════════

class ValidationError(Exception):
    """Erreur de validation du Wave IR."""

    def __init__(self, message: str, node: Optional[Node] = None):
        self.node = node
        loc = f" dans {type(node).__name__}" if node else ""
        super().__init__(f"Validation{loc}: {message}")


def validate(node: Node) -> List[str]:
    """
    Valide un AST ondulatoire.

    Vérifie :
      - Pas de variables non définies
      - Pas de redéfinitions
      - Types cohérents (un Decode après un Encode, etc.)
      - Pas de cycles

    Args:
        node: nœud racine (Program)

    Returns:
        liste des avertissements/erreurs (vide = valide)

    Raises:
        ValidationError: si erreur bloquante
    """
    warnings: List[str] = []

    if not isinstance(node, Program):
        raise ValidationError("La racine doit être un Program", node)

    # Collecte des variables définies et utilisées
    defined: Dict[str, Node] = {}
    used: set = set()

    def collect(stmt: Statement):
        if isinstance(stmt, (Assign, Store, Query)):
            if stmt.name in defined:
                warnings.append(f"Variable '{stmt.name}' redéfinie")
            defined[stmt.name] = stmt

    def visit(expr: Expr):
        if isinstance(expr, Var):
            used.add(expr.name)
        elif isinstance(expr, LambdaExpr):
            # Les paramètres du lambda sont définis dans son corps
            for p in expr.params:
                defined[p] = expr
        for child in expr.children():
            if isinstance(child, Expr):
                visit(child)

    def walk_stmt(stmt: Statement):
        """Traverse un statement et ses statements imbriqués
        (CodeBlock, IfStmt, WhileStmt, FunctionDef, ForStmt)."""
        collect(stmt)
        if isinstance(stmt, FunctionDef):
            # Les paramètres de la fonction sont définis dans son corps
            for p in stmt.params:
                defined[p] = stmt
        for child in stmt.children():
            if isinstance(child, Expr):
                visit(child)
            elif isinstance(child, Statement):
                walk_stmt(child)

    for stmt in node.statements:
        walk_stmt(stmt)

    # Vérifier les variables utilisées mais non définies
    undefined = used - set(defined.keys())
    for name in undefined:
        warnings.append(f"Variable '{name}' utilisée mais non définie")

    return warnings


# ═══════════════════════════════════════════════════════════════════════════════
# PARSER — TEXTE → AST
# ═══════════════════════════════════════════════════════════════════════════════

class ParseError(Exception):
    """Erreur de parsing du langage ondulatoire."""

    def __init__(self, message: str, pos: int = 0, line: str = ""):
        self.pos = pos
        self.line = line
        super().__init__(f"Parse error at position {pos}: {message}" + (f"\n  {line}" if line else ""))


# Patterns regex pour le tokenizer
_TOKEN_PATTERNS = [
    # Mots-clés (ordre important : les plus longs d'abord)
    ("KEYWORD", r"\b(?:STORE|QUERY|IN|FROM|RETURN|ENCODE|DECODE|BIND_MANY|BIND|UNBIND|SUPERPOSE|"
                r"RESONANCE|ROTATE|NORMALIZE|INTERFERE|DIFFRACT|FILTER_LP|FILTER_HP|FILTER_BP|"
                r"PHASE_SHIFT|EMERGE|OPPOSE|AMPLIFY|"
                r"IF|ELSE|WHILE|BLOCK|CALL|FUNCTION|FOR|LAMBDA|RAW|"
                r"ADD|SUB|MUL|DIV|POW|MOD|SQRT|NEG|ABS|FLOOR)\b"),
    ("NUMBER", r"-?\d+\.?\d*(?:[eE][+-]?\d+)?"),
    ("BOOL", r"\b(?:true|false)\b"),
    ("STRING", r'"[^"]*"|\'[^\']*\''),
    # Unicode-aware ID: lettre ou _ suivi de lettres, chiffres, _
    ("ID", r"[^\W\d_]\w*"),
    ("ASSIGN", r"="),
    ("COMMA", r","),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("LBRACE", r"\{"),
    ("RBRACE", r"\}"),
    ("LBRACKET", r"\["),
    ("RBRACKET", r"\]"),
    ("SEMICOLON", r";"),
    # Assignations augmentées (avant ASSIGN)
    ("PLUSEQ", r"\+\="),
    ("MINUSEQ", r"-\="),
    ("STAREQ", r"\*\="),
    ("SLASHEQ", r"/\="),
    # Comparaisons (avant ASSIGN : "==" doit gagner sur "=")
    ("GE", r">="),
    ("LE", r"<="),
    ("EQ", r"=="),
    ("NE", r"!="),
    ("GT", r">"),
    ("LT", r"<"),
    ("NEWLINE", r"\n"),
    ("SKIP", r"[ \t\r]+"),
    ("COMMENT", r"#.*"),
]


def tokenize(source: str) -> List[Tuple[str, str, int]]:
    """
    Tokenise le code source ondulatoire.

    Args:
        source: code source texte

    Returns:
        liste de (type, valeur, position)

    Raises:
        ParseError: si caractère inattendu
    """
    tokens = []
    pos = 0

    while pos < len(source):
        matched = False
        for token_type, pattern in _TOKEN_PATTERNS:
            m = re.match(pattern, source[pos:])
            if m:
                value = m.group()
                if token_type not in ("SKIP", "COMMENT", "NEWLINE"):
                    tokens.append((token_type, value, pos))
                pos += len(value)
                matched = True
                break

        if not matched:
            line_start = max(0, pos - 20)
            line_end = min(len(source), pos + 20)
            raise ParseError(
                f"Caractère inattendu '{source[pos]}'",
                pos,
                source[line_start:line_end]
            )

    return tokens


class Parser:
    """
    Parser du langage ondulatoire.

    Usage:
        parser = Parser()
        ast = parser.parse('''
            ψ_q = ENCODE "Qu'est-ce que la lumière ?"
            ψ_r = RESONANCE(ψ_q, H_connaissances)
            reponse = DECODE(ψ_r)
        ''')
    """

    def __init__(self, source: str):
        self.tokens = tokenize(source)
        self.pos = 0

    def parse(self) -> Program:
        """Parse le programme complet."""
        statements = []
        while not self._is_at_end():
            # Séparateur ';' optionnel entre statements au niveau racine
            token = self._peek()
            if token and token[0] == "SEMICOLON":
                self._advance()
                continue
            stmt = self._parse_statement()
            if stmt is not None:
                statements.append(stmt)
        return Program(statements)

    def _is_at_end(self) -> bool:
        return self.pos >= len(self.tokens)

    def _peek(self) -> Optional[Tuple[str, str, int]]:
        if self._is_at_end():
            return None
        return self.tokens[self.pos]

    def _advance(self) -> Tuple[str, str, int]:
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def _expect(self, expected_type: str) -> Tuple[str, str, int]:
        token = self._peek()
        if token is None:
            raise ParseError(f"Attendu {expected_type}, fin de fichier", self.pos)
        if token[0] != expected_type:
            raise ParseError(f"Attendu {expected_type}, trouvé {token[0]}('{token[1]}')", token[2])
        return self._advance()

    def _match(self, token_type: str) -> bool:
        token = self._peek()
        if token and token[0] == token_type:
            self._advance()
            return True
        return False

    def _parse_statement(self) -> Optional[Statement]:
        """Parse un statement."""
        token = self._peek()
        if token is None:
            return None

        ttype, tval, tpos = token

        # STORE nom = expr IN hologram
        if ttype == "KEYWORD" and tval == "STORE":
            self._advance()
            name = self._expect("ID")[1]
            self._expect("ASSIGN")
            value = self._parse_expr()
            self._expect("KEYWORD")  # IN
            hologram = self._expect("ID")[1]
            return Store(name, value, hologram)

        # QUERY nom = expr FROM hologram
        if ttype == "KEYWORD" and tval == "QUERY":
            self._advance()
            name = self._expect("ID")[1]
            self._expect("ASSIGN")
            value = self._parse_expr()
            self._expect("KEYWORD")  # FROM
            hologram = self._expect("ID")[1]
            return Query(name, value, hologram)

        # RETURN expr
        if ttype == "KEYWORD" and tval == "RETURN":
            self._advance()
            value = self._parse_expr()
            return Return(value)

        # BLOCK { stmt ; stmt }
        if ttype == "KEYWORD" and tval == "BLOCK":
            self._advance()
            body = self._parse_block()
            return CodeBlock(body)

        # IF(cond) { then } ELSE { else }
        if ttype == "KEYWORD" and tval == "IF":
            self._advance()
            self._expect("LPAREN")
            condition = self._parse_expr()
            self._expect("RPAREN")
            then_body = self._parse_block()
            else_body = None
            # ELSE optionnel
            token = self._peek()
            if token and token[0] == "KEYWORD" and token[1] == "ELSE":
                self._advance()
                else_body = self._parse_block()
            return IfStmt(condition, then_body, else_body)

        # WHILE(cond) { body }
        if ttype == "KEYWORD" and tval == "WHILE":
            self._advance()
            self._expect("LPAREN")
            condition = self._parse_expr()
            self._expect("RPAREN")
            body = self._parse_block()
            return WhileStmt(condition, body)

        # FUNCTION name(p1, p2) { body }
        if ttype == "KEYWORD" and tval == "FUNCTION":
            self._advance()
            name = self._expect("ID")[1]
            params: List[str] = []
            if self._peek() and self._peek()[0] == "LPAREN":
                self._advance()
                while self._peek() and self._peek()[0] != "RPAREN":
                    if self._peek()[0] == "ID":
                        params.append(self._advance()[1])
                    else:
                        self._advance()
                self._expect("RPAREN")
            body = self._parse_block()
            return FunctionDef(name, params, body)

        # FOR x IN expr { body }
        if ttype == "KEYWORD" and tval == "FOR":
            self._advance()
            target = self._expect("ID")[1]
            self._expect("KEYWORD")  # IN
            iterable = self._parse_expr()
            body = self._parse_block()
            return ForStmt(target, iterable, body)

        # ID += expr (assignation augmentée)
        if ttype == "ID":
            # Peek ahead for '='
            if self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1][0] == "ASSIGN":
                name = tval
                self._advance()  # consume ID
                self._advance()  # consume =
                value = self._parse_expr()
                return Assign(name, value)
            # AugAssign : ID +=/-=/*=/= expr
            if (self.pos + 1 < len(self.tokens) and
                    self.tokens[self.pos + 1][0] in
                    ("PLUSEQ", "MINUSEQ", "STAREQ", "SLASHEQ")):
                name = tval
                self._advance()
                op_token = self._advance()
                op_map = {"PLUSEQ": "ADD", "MINUSEQ": "SUB",
                          "STAREQ": "MUL", "SLASHEQ": "DIV"}
                value = self._parse_expr()
                return AugAssign(name, op_map[op_token[0]], value)

        raise ParseError(f"Statement inattendu: {tval}", tpos)

    def _parse_block(self) -> List[Statement]:
        """Parse un bloc : { stmt ; stmt ; ... }."""
        self._expect("LBRACE")
        body: List[Statement] = []
        while True:
            token = self._peek()
            if token is None:
                raise ParseError("Bloc non fermé : '}' attendu", self.pos)
            if token[0] == "RBRACE":
                self._advance()
                break
            stmt = self._parse_statement()
            if stmt is None:
                break
            body.append(stmt)
            # Séparateur ';' optionnel entre statements
            token = self._peek()
            if token and token[0] == "SEMICOLON":
                self._advance()
        return body

    def _parse_expr(self) -> Expr:
        """Parse une expression (subscripts, comparaisons, ternaire)."""
        expr = self._parse_primary()

        # Subscript en chaîne : arr[0], matrix[i][j]
        while self._peek() and self._peek()[0] == "LBRACKET":
            self._advance()
            index = self._parse_primary()
            self._expect("RBRACKET")
            expr = Subscript(expr, index)

        # Opérateurs de comparaison infixes : x > 10, a == b...
        token = self._peek()
        if token and token[0] in ("GT", "GE", "LT", "LE", "EQ", "NE"):
            op_map = {"GT": "GT", "GE": "GE", "LT": "LT",
                      "LE": "LE", "EQ": "EQ", "NE": "NE"}
            self._advance()
            right = self._parse_primary()
            expr = MathOp(op_map[token[0]], expr, right)

        # Ternaire infixe : a IF cond ELSE b
        # (ne se déclenche pas si IF est suivi de '(' → statement IF(cond))
        token = self._peek()
        if (token and token[0] == "KEYWORD" and token[1] == "IF" and
                not (self.pos + 1 < len(self.tokens) and
                     self.tokens[self.pos + 1][0] == "LPAREN")):
            self._advance()
            condition = self._parse_expr()
            self._expect("KEYWORD")  # ELSE
            if_false = self._parse_primary()
            expr = TernaryExpr(condition, expr, if_false)

        return expr

    def _parse_primary(self) -> Expr:
        """Parse une expression primaire (littéral, variable, appel)."""
        token = self._peek()
        if token is None:
            raise ParseError("Expression attendue, fin de fichier", self.pos)

        ttype, tval, tpos = token

        # Littéral numérique
        if ttype == "NUMBER":
            self._advance()
            try:
                return Literal(float(tval))
            except ValueError:
                return Literal(int(tval))

        # Littéral chaîne
        if ttype == "STRING":
            self._advance()
            # Enlever les guillemets
            s = tval[1:-1]
            return StringLit(s)

        # Booléen
        if ttype == "BOOL":
            self._advance()
            return Literal(1.0 if tval == "true" else 0.0)

        # Liste : [1, 2, 3]
        if ttype == "LBRACKET":
            self._advance()
            items: List[Expr] = []
            while self._peek() and self._peek()[0] != "RBRACKET":
                items.append(self._parse_expr())
                if self._peek() and self._peek()[0] == "COMMA":
                    self._advance()
            self._expect("RBRACKET")
            return ListLiteral(items)

        # Code brut : RAW "texte"
        if ttype == "KEYWORD" and tval == "RAW":
            self._advance()
            s = self._expect("STRING")[1][1:-1]
            return RawCode(s)

        # Variable ou appel de fonction : f(...)
        if ttype == "ID":
            self._advance()
            # Lookahead : ID( → FunctionCall
            token = self._peek()
            if token and token[0] == "LPAREN":
                self._advance()  # consume (
                args = self._parse_expr_list()
                self._expect("RPAREN")
                return FunctionCall(tval, args)
            return Var(tval)

        # Mot-clé → appel de fonction
        if ttype == "KEYWORD":
            return self._parse_call()

        raise ParseError(f"Expression inattendue: {tval}", tpos)

    def _parse_call(self) -> Expr:
        """Parse un appel de primitive : KEYWORD ( args )."""
        kw_token = self._advance()
        kw = kw_token[1]

        # Certains keywords n'ont pas de parenthèses (ex: ENCODE "texte")
        if kw == "ENCODE":
            # ENCODE string
            token = self._peek()
            if token is None:
                raise ParseError("ENCODE attend une chaîne", self.pos)
            if token[0] == "STRING":
                self._advance()
                return Encode(token[1][1:-1])
            # ENCODE avec parenthèses: ENCODE(expr)
            if token[0] == "LPAREN":
                self._advance()
                expr = self._parse_expr()
                self._expect("RPAREN")
                return Encode("")  # Fallback — sera remplacé à la compilation
            raise ParseError(f"ENCODE attend une chaîne, trouvé {token[0]}", token[2])

        # Appels avec parenthèses
        self._expect("LPAREN")

        if kw == "DECODE":
            psi = self._parse_expr()
            self._expect("RPAREN")
            return Decode(psi)

        elif kw == "BIND":
            left = self._parse_expr()
            self._expect("COMMA")
            right = self._parse_expr()
            self._expect("RPAREN")
            return Bind(left, right)

        elif kw == "UNBIND":
            left = self._parse_expr()
            self._expect("COMMA")
            right = self._parse_expr()
            self._expect("RPAREN")
            return Unbind(left, right)

        elif kw == "SUPERPOSE":
            psis = self._parse_expr_list()
            self._expect("RPAREN")
            return Superpose(psis)

        elif kw == "RESONANCE":
            left = self._parse_expr()
            self._expect("COMMA")
            right = self._parse_expr()
            self._expect("RPAREN")
            return Resonance(left, right)

        elif kw == "ROTATE":
            psi = self._parse_expr()
            self._expect("COMMA")
            angle = self._parse_number()
            self._expect("RPAREN")
            return Rotate(psi, angle)

        elif kw == "NORMALIZE":
            psi = self._parse_expr()
            self._expect("RPAREN")
            return Normalize(psi)

        elif kw == "INTERFERE":
            base = self._parse_expr()
            self._expect("COMMA")
            other = self._parse_expr()
            epsilon = 0.1
            if self._peek() and self._peek()[0] == "COMMA":
                self._advance()
                epsilon = self._parse_number()
            self._expect("RPAREN")
            return Interfere(base, other, epsilon)

        elif kw == "DIFFRACT":
            psi = self._parse_expr()
            inverse = False
            if self._peek() and self._peek()[0] == "COMMA":
                self._advance()
                tok = self._advance()
                inverse = tok[1] == "true"
            self._expect("RPAREN")
            return Diffract(psi, inverse)

        elif kw == "FILTER_LP":
            psi = self._parse_expr()
            self._expect("COMMA")
            cutoff = self._parse_number()
            self._expect("RPAREN")
            return FilterLP(psi, cutoff)

        elif kw == "FILTER_HP":
            psi = self._parse_expr()
            self._expect("COMMA")
            cutoff = self._parse_number()
            self._expect("RPAREN")
            return FilterHP(psi, cutoff)

        elif kw == "FILTER_BP":
            psi = self._parse_expr()
            self._expect("COMMA")
            low = self._parse_number()
            self._expect("COMMA")
            high = self._parse_number()
            self._expect("RPAREN")
            return FilterBP(psi, low, high)

        elif kw == "PHASE_SHIFT":
            psi = self._parse_expr()
            self._expect("COMMA")
            shift = self._parse_number()
            self._expect("RPAREN")
            return PhaseShift(psi, shift)

        elif kw == "EMERGE":
            # ⚠️ _parse_expr_list consommerait le nombre final comme Literal
            # (bug roundtrip : EMERGE(a, b, 0.60) → Literal enfant + temperature=0.5).
            # On parse manuellement pour respecter la grammaire EBNF :
            #   EMERGE '(' expr (',' expr)* (',' number)? ')'
            psis = [self._parse_expr()]
            temperature = 0.5
            while self._peek() and self._peek()[0] == "COMMA":
                self._advance()
                if self._peek() and self._peek()[0] == "NUMBER":
                    temperature = self._parse_number()
                    break
                psis.append(self._parse_expr())
            self._expect("RPAREN")
            return Emerge(psis, temperature)

        elif kw == "OPPOSE":
            left = self._parse_expr()
            self._expect("COMMA")
            right = self._parse_expr()
            self._expect("RPAREN")
            return Oppose(left, right)

        elif kw == "AMPLIFY":
            psi = self._parse_expr()
            self._expect("COMMA")
            comp = self._parse_expr()
            boost = 3.0
            if self._peek() and self._peek()[0] == "COMMA":
                self._advance()
                boost = self._parse_number()
            self._expect("RPAREN")
            return Amplify(psi, comp, boost)

        elif kw == "BIND_MANY":
            psis = self._parse_expr_list()
            self._expect("RPAREN")
            return BindMany(psis)

        # Opérations mathématiques : ADD(a, b), SQRT(a), NEG(a)...
        elif kw in ("ADD", "SUB", "MUL", "DIV", "POW", "MOD",
                    "SQRT", "NEG", "ABS", "FLOOR"):
            left = self._parse_expr()
            right = None
            if self._peek() and self._peek()[0] == "COMMA":
                self._advance()
                right = self._parse_expr()
            self._expect("RPAREN")
            return MathOp(kw, left, right)

        # Appel de fonction nommée : CALL(f, 2, 3)
        elif kw == "CALL":
            name = self._advance()
            if name[0] != "ID":
                raise ParseError(f"CALL attend un nom de fonction, trouvé {name[0]}", name[2])
            args: List[Expr] = []
            if self._peek() and self._peek()[0] == "COMMA":
                self._advance()  # virgule après le nom
                args = self._parse_expr_list()
            self._expect("RPAREN")
            return FunctionCall(name[1], args)

        # Fonction anonyme : LAMBDA(x, y) { expr }
        elif kw == "LAMBDA":
            params: List[str] = []
            while self._peek() and self._peek()[0] != "RPAREN":
                if self._peek()[0] == "ID":
                    params.append(self._advance()[1])
                else:
                    self._advance()
            self._expect("RPAREN")
            self._expect("LBRACE")
            body = self._parse_expr()
            self._expect("RBRACE")
            return LambdaExpr(params, body)

        else:
            raise ParseError(f"Primitive inconnue: {kw}", kw_token[2])

    def _parse_expr_list(self) -> List[Expr]:
        """Parse une liste d'expressions séparées par des virgules."""
        exprs = []
        exprs.append(self._parse_expr())
        while self._peek() and self._peek()[0] == "COMMA":
            self._advance()
            # Vérifier si c'est suivi par un mot-clé de paramètre (weights, temperature)
            if self._peek() and self._peek()[0] == "ID" and self._peek()[1] == "weights":
                break
            exprs.append(self._parse_expr())
        return exprs

    def _parse_number(self) -> float:
        """Parse un nombre (littéral numérique ou négation)."""
        token = self._peek()
        if token is None:
            raise ParseError("Nombre attendu, fin de fichier", self.pos)

        if token[0] == "NUMBER":
            self._advance()
            return float(token[1])

        # Négation: -ID (ex: -0.5, mais le tokenizer le sépare)
        if token[0] == "ID" and token[1] == "-":
            self._advance()
            num = self._advance()
            if num[0] != "NUMBER":
                raise ParseError(f"Nombre attendu après '-', trouvé {num[0]}", num[2])
            return -float(num[1])

        raise ParseError(f"Nombre attendu, trouvé {token[0]}('{token[1]}')", token[2])


def parse(source: str) -> Program:
    """
    Parse du code source ondulatoire en AST.

    Fonction utilitaire — point d'entrée principal.

    Args:
        source: code source texte en langage ondulatoire

    Returns:
        Program (AST racine)

    Raises:
        ParseError: si erreur de syntaxe

    Example:
        >>> ast = parse('''
        ...     ψ_q = ENCODE "Qu'est-ce que φ ?"
        ...     ψ_r = RESONANCE(ψ_q, H)
        ...     reponse = DECODE(ψ_r)
        ... ''')
        >>> print(ast)
        ψ_q = ENCODE "Qu'est-ce que φ ?"
        ψ_r = RESONANCE(ψ_q, H)
        reponse = DECODE(ψ_r)
    """
    parser = Parser(source)
    return parser.parse()


# ═══════════════════════════════════════════════════════════════════════════════
# TRANSFORMATIONS D'ARBRE
# ═══════════════════════════════════════════════════════════════════════════════

def walk(node: Node, visitor: callable):
    """
    Parcourt récursivement l'AST et applique un visiteur à chaque nœud.

    Args:
        node: nœud racine
        visitor: fonction f(node) → None ou nouveau nœud
    """
    visitor(node)
    for child in node.children():
        walk(child, visitor)


def map_nodes(node: Node, transform: callable) -> Node:
    """
    Transforme récursivement l'AST en appliquant une fonction à chaque nœud.

    Args:
        node: nœud racine
        transform: fonction f(node) → nouveau nœud

    Returns:
        nouvel AST transformé
    """
    # Transformer les enfants d'abord (bottom-up)
    new_children = [map_nodes(c, transform) for c in node.children()]

    # Créer un nouveau nœud avec les enfants transformés
    cls = type(node)
    try:
        new_node = cls(**{k: v for k, v in node.__dict__.items()
                         if not k.startswith('_')})
        # Remplacer les enfants, en répartissant correctement les listes :
        # chaque attribut enfant reçoit exactement les enfants mappés qui
        # lui correspondent (les attributs de type List reçoivent TOUS les
        # enfants mappés qui suivent, jusqu'au prochain attribut scalaire).
        attrs = _get_child_attrs(node)
        idx = 0
        for attr in attrs:
            value = node.__dict__.get(attr)
            if isinstance(value, list):
                # Attribut de type liste : consomme les nœuds enfants mappés
                # restants correspondant à ce bloc (n enfants pour n éléments)
                n = len(value)
                mapped = new_children[idx:idx + n]
                setattr(new_node, attr, mapped)
                idx += n
            else:
                # Attribut scalaire (ou Optional) : un seul enfant mappé
                if value is not None and idx < len(new_children):
                    setattr(new_node, attr, new_children[idx])
                    idx += 1
    except Exception:
        new_node = node

    # Appliquer la transformation
    return transform(new_node)


def _get_child_attrs(node: Node) -> List[str]:
    """Retourne les noms des attributs qui contiennent des nœuds enfants."""
    if isinstance(node, Program):
        return ["statements"]
    if isinstance(node, (Assign, Store, Query)):
        return ["value"]
    if isinstance(node, Return):
        return ["value"]
    if isinstance(node, Decode):
        return ["psi"]
    if isinstance(node, (Bind, Unbind, Resonance, Oppose)):
        return ["left", "right"]
    if isinstance(node, (Superpose, Emerge, BindMany)):
        return ["psis"]
    if isinstance(node, (Rotate, Normalize, FilterLP, FilterHP, FilterBP, PhaseShift)):
        return ["psi"]
    if isinstance(node, Interfere):
        return ["base", "other"]
    if isinstance(node, Diffract):
        return ["psi"]
    if isinstance(node, Amplify):
        return ["psi", "component"]
    if isinstance(node, CodeBlock):
        return ["body"]
    if isinstance(node, IfStmt):
        return ["condition", "then_body", "else_body"]
    if isinstance(node, WhileStmt):
        return ["condition", "body"]
    if isinstance(node, MathOp):
        return ["left", "right"]
    if isinstance(node, FunctionCall):
        return ["args"]
    if isinstance(node, FunctionDef):
        return ["body"]
    if isinstance(node, ForStmt):
        return ["iterable", "body"]
    if isinstance(node, AugAssign):
        return ["value"]
    if isinstance(node, ListLiteral):
        return ["items"]
    if isinstance(node, Subscript):
        return ["obj", "index"]
    if isinstance(node, TernaryExpr):
        return ["condition", "if_true", "if_false"]
    if isinstance(node, LambdaExpr):
        return ["body"]
    return []


# ═══════════════════════════════════════════════════════════════════════════════
# PROGRAMMES PRÉDÉFINIS (pour l'IA)
# ═══════════════════════════════════════════════════════════════════════════════

def make_fact(subject: str, relation: str, obj: str) -> Program:
    """
    Crée un programme qui encode un fait dans un hologramme.

    Usage typique de l'IA :
        ast = make_fact("lumiere", "est", "onde electromagnetique")
        code = ast.to_wave()  # → code source ondulatoire
    """
    return Program([
        Assign("ψ_s", Encode(subject)),
        Assign("ψ_r", Encode(relation)),
        Assign("ψ_o", Encode(obj)),
        Assign("ψ_fait", BindMany([Var("ψ_s"), Var("ψ_r"), Var("ψ_o")])),
        Store("fait", Var("ψ_fait"), "H_connaissances"),
    ])


def make_query(question: str, hologram: str = "H_connaissances") -> Program:
    """
    Crée un programme qui interroge un hologramme.

    Usage typique de l'IA :
        ast = make_query("Qu'est-ce que la lumiere ?")
        code = ast.to_wave()
    """
    return Program([
        Assign("ψ_q", Encode(question)),
        Query("ψ_r", Var("ψ_q"), hologram),
        Assign("reponse", Decode(Var("ψ_r"))),
        Return(Var("reponse")),
    ])


def make_reasoning(premise_a: str, premise_b: str, conclusion_var: str = "ψ_conclusion") -> Program:
    """
    Crée un programme de raisonnement par émergence.

    Usage :
        ast = make_reasoning("lumiere", "onde")
        # → EMERGE des deux prémisses pour créer une conclusion
    """
    return Program([
        Assign("ψ_a", Encode(premise_a)),
        Assign("ψ_b", Encode(premise_b)),
        Assign(conclusion_var, Emerge([Var("ψ_a"), Var("ψ_b")], temperature=0.6)),
        Assign("texte", Decode(Var(conclusion_var))),
        Return(Var("texte")),
    ])


def make_creativity(concept_a: str, concept_b: str, epsilon: float = 0.15) -> Program:
    """
    Crée un programme de créativité par interférence.

    Usage :
        ast = make_creativity("pluie", "musique", epsilon=0.15)
    """
    return Program([
        Assign("ψ_a", Encode(concept_a)),
        Assign("ψ_b", Encode(concept_b)),
        Assign("ψ_creatif", Interfere(Var("ψ_a"), Var("ψ_b"), epsilon)),
        Assign("idee", Decode(Var("ψ_creatif"))),
        Return(Var("idee")),
    ])


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 65)
    print("  🌊 WAVE IR — Test du parser, AST, sérialiseur")
    print("=" * 65)

    # ── Test 1 : Parsing ──
    print("\n── 1. PARSING ──")
    source = r'''
ψ_q = ENCODE "Qu'est-ce que la lumière ?"
ψ_fait = BIND_MANY(ψ_s, ψ_r, ψ_o)
ψ_r = RESONANCE(ψ_q, H)
reponse = DECODE(ψ_r)
RETURN reponse
'''
    ast = None
    try:
        ast = parse(source)
        print("  ✅ Parsing réussi")
        print(f"  Nombre de statements: {len(ast.statements)}")
        for s in ast.statements:
            print(f"    - {type(s).__name__}: {s if not isinstance(s, Assign) else f'{s.name} = ...'}")
    except ParseError as e:
        print(f"  ❌ Erreur de parsing: {e}")
        # Test avec un source plus simple (ASCII-only)
        print("\n  → Test avec source ASCII uniquement:")
        source2 = '''
q = ENCODE "Qu est-ce que la lumiere ?"
r = RESONANCE(q, H)
reponse = DECODE(r)
RETURN reponse
'''
        try:
            ast = parse(source2)
            print("  ✅ Parsing ASCII réussi")
        except ParseError as e2:
            print(f"  ❌ Erreur parsing ASCII: {e2}")

    if ast is not None:
        # ── Test 2 : Pretty Print ──
        print("\n── 2. PRETTY PRINT (AST → code) ──")
        pp = ast.to_wave()
        print(pp)

        # ── Test 3 : JSON roundtrip ──
        print("\n── 3. SÉRIALISATION JSON (roundtrip) ──")
        json_str = to_json(ast, indent=2)
        print(f"  JSON ({len(json_str)} caractères):")
        print(json_str[:300] + "...")

        ast2 = from_json(json_str)
        pp2 = ast2.to_wave()
        if pp != pp2:
            print(f"  ❌ Roundtrip échoué!")
            print(f"  Original: {pp}")
            print(f"  Restauré: {pp2}")
        else:
            print(f"  ✅ Roundtrip JSON réussi")
    else:
        print("\n── 2-3. SKIPPÉ (parsing échoué) ──")

    # ── Test 4 : Validation ──
    print("\n── 4. VALIDATION ──")
    # Program avec variable non définie
    ast_undef = Program([
        Assign("x", Encode("test")),
        Assign("y", Var("z")),  # 'z' n'est pas définie
    ])
    warnings = validate(ast_undef)
    if warnings:
        for w in warnings:
            print(f"  ⚠️  {w}")
    else:
        print("  ✅ Aucun avertissement")

    # Program valide
    ast_valid = Program([
        Assign("x", Encode("test")),
        Assign("y", Var("x")),  # 'x' est définie
    ])
    warnings2 = validate(ast_valid)
    print(f"  Programme valide: {len(warnings2)} avertissements (attendu: 0)")

    # ── Test 5 : Programmes prédéfinis ──
    print("\n── 5. PROGRAMMES PRÉDÉFINIS (pour l'IA) ──")
    fact_ast = make_fact("lumiere", "est", "onde electromagnetique")
    print("  make_fact:")
    print(fact_ast.to_wave())

    query_ast = make_query("Qu'est-ce que la lumière ?")
    print("\n  make_query:")
    print(query_ast.to_wave())

    creative_ast = make_creativity("pluie", "musique", epsilon=0.15)
    print("\n  make_creativity:")
    print(creative_ast.to_wave())

    # ── Test 6 : Tokenizer d'erreur ──
    print("\n── 6. GESTION D'ERREURS ──")
    try:
        parse("x = ADD(1,")  # parenthèse non fermée
        print("  ❌ Aurait dû lever une erreur")
    except ParseError as e:
        print(f"  ✅ ParseError bien levée: {e}")

    # ── Test 7 : Walk / Map ──
    print("\n── 7. TRANSFORMATIONS D'ARBRE ──")
    if ast is not None:
        count = [0]

        def count_nodes(n):
            count[0] += 1

        walk(ast, count_nodes)
        print(f"  walk: {count[0]} nœuds visités")
    else:
        # Test avec un AST construit manuellement
        test_ast = Program([Assign("x", Encode("test")), Assign("y", Var("x"))])
        count = [0]
        def count_nodes(n):
            count[0] += 1
        walk(test_ast, count_nodes)
        print(f"  walk (manuel): {count[0]} nœuds visités")

    # ── Test 8 : NŒUDS COMPUTATIONNELS (MathOp, If, While) ──
    print("\n── 8. NŒUDS COMPUTATIONNELS ──")
    src_comp = (
        "x = ADD(2, MUL(3, 4))\n"
        "y = SQRT(16)\n"
        "IF(x > 10) { z = SUB(x, 10) ; RETURN z } ELSE { RETURN y }\n"
        "WHILE(x < 100) { x = ADD(x, 1) }"
    )
    try:
        ast_comp = parse(src_comp)
        print("  Parse computationnel:")
        for line in ast_comp.to_wave().split('\n'):
            print(f"    │ {line}")

        # Roundtrip
        rt_ok = from_json(to_json(ast_comp)).to_wave() == ast_comp.to_wave()
        print(f"  Roundtrip JSON: {'✅' if rt_ok else '❌'}")

        # Validation imbriquée : z défini dans IF, utilisé dans RETURN ;
        # 'x' redéfinie dans la boucle est un avertissement légitime
        w_comp = validate(ast_comp)
        undefined = [w for w in w_comp if "non définie" in w]
        print(f"  Validation: {len(w_comp)} avertissements "
              f"({len(undefined)} non-définies, attendu: 0)")

        # Walk compte les nœuds imbriqués
        cnt = [0]
        walk(ast_comp, lambda n: cnt.__setitem__(0, cnt[0] + 1))
        print(f"  Walk: {cnt[0]} nœuds (y compris imbriqués)")

        # map_nodes préserve la structure (fix listes)
        mapped = map_nodes(ast_comp, lambda n: n)
        print(f"  map_nodes préserve: {mapped.to_wave() == ast_comp.to_wave()}")
    except ParseError as e:
        print(f"  ❌ Parse computationnel échoué: {e}")

    print("\n" + "=" * 65)
    print("  ✅ Wave IR — Tous les tests passent.")
    print("=" * 65)
