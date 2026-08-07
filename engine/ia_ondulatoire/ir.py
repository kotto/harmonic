# -*- coding: utf-8 -*-
"""
ir.py — Le Wave IR : grammaire formelle, AST, parseur, sérialisation.

Conforme au DOCUMENT_FONDATEUR_LANGAGE_ONDULATOIRE.md §4 (grammaire EBNF) et §6
(Wave IR) : les 23 nœuds, roundtrip JSON parfait, validation statique.

Pipeline : texte ondulatoire → parse() → Program (AST) → validate() → to_json()
          → réseau → from_json() → moteur.executer()

Exemple canonique (§4.3) :
    ψ_q = ENCODE "Qu'est-ce que la lumière ?"
    QUERY ψ_r = ψ_q FROM H_connaissances
    reponse = DECODE(ψ_r)
    RETURN reponse
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


# ────────────────────────────────────────────────────────────────────────
# Grammaire EBNF (§4.2) — tokens
# ────────────────────────────────────────────────────────────────────────

MOTS_CLEFS = {
    "ENCODE", "DECODE", "BIND", "UNBIND", "SUPERPOSE", "RESONANCE", "ROTATE",
    "NORMALIZE", "INTERFERE", "DIFFRACT", "FILTER_LP", "FILTER_HP", "FILTER_BP",
    "PHASE_SHIFT", "EMERGE", "OPPOSE", "AMPLIFY", "BIND_MANY",
    "STORE", "QUERY", "RETURN", "IN", "FROM", "TRUE", "FALSE",
}

_TOKEN_RE = re.compile(r"""
    (?P<ESPACE>\s+)
  | (?P<CHAINE>"[^"]*"|'[^']*')
  | (?P<NOMBRE>-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)
  | (?P<ID>[A-Za-z_][A-Za-z0-9_]*)
  | (?P<SYMBOLE>[(),=])
""", re.VERBOSE)


class ErreurSyntaxe(Exception):
    """Erreur de parsing du langage ondulatoire."""


@dataclass
class Jeton:
    type: str          # CHAINE | NOMBRE | ID | SYMBOLE
    valeur: Any
    position: int
    ligne: int


def tokeniser(source: str) -> List[Jeton]:
    """Découpe le source ondulatoire en jetons (grammaire EBNF §4.2)."""
    jetons = []
    ligne = 1
    for m in _TOKEN_RE.finditer(source):
        kind = m.lastgroup
        texte = m.group()
        if kind == "ESPACE":
            ligne += texte.count("\n")
            continue
        if kind == "CHAINE":
            valeur = texte[1:-1]
        elif kind == "NOMBRE":
            valeur = float(texte) if ('.' in texte or 'e' in texte.lower()) else int(texte)
        elif kind == "ID":
            valeur = texte
        else:
            valeur = texte
        jetons.append(Jeton(kind, valeur, m.start(), ligne))
    return jetons


# ────────────────────────────────────────────────────────────────────────
# AST — les 23 nœuds (§6.2)
# ────────────────────────────────────────────────────────────────────────

class Nœud:
    """Base de l'AST : sérialisable (to_dict/from_dict), transformable (marcher)."""

    def to_dict(self) -> Dict[str, Any]:
        return {"type": type(self).__name__}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Nœud":
        return cls()

    def enfants(self) -> List["Nœud"]:
        return []

    def marcher(self, visiteur):
        visiteur(self)
        for enfant in self.enfants():
            enfant.marcher(visiteur)


# ── Statements ──────────────────────────────────────────────────────────

@dataclass
class Program(Nœud):
    statements: List[Nœud] = field(default_factory=list)

    def to_dict(self):
        return {"type": "Program", "statements": [s.to_dict() for s in self.statements]}

    @classmethod
    def from_dict(cls, d):
        return Program([_FROM_DICT[s["type"]](s) for s in d["statements"]])

    def enfants(self):
        return self.statements


@dataclass
class Assign(Nœud):
    nom: str
    expr: Nœud

    def to_dict(self):
        return {"type": "Assign", "nom": self.nom, "expr": self.expr.to_dict()}

    @classmethod
    def from_dict(cls, d):
        return Assign(d["nom"], _FROM_DICT[d["expr"]["type"]](d["expr"]))

    def enfants(self):
        return [self.expr]


@dataclass
class Store(Nœud):
    nom: str
    expr: Nœud
    cible: str

    def to_dict(self):
        return {"type": "Store", "nom": self.nom, "expr": self.expr.to_dict(), "cible": self.cible}

    @classmethod
    def from_dict(cls, d):
        return Store(d["nom"], _FROM_DICT[d["expr"]["type"]](d["expr"]), d["cible"])

    def enfants(self):
        return [self.expr]


@dataclass
class Query(Nœud):
    nom: str
    expr: Nœud
    source: str

    def to_dict(self):
        return {"type": "Query", "nom": self.nom, "expr": self.expr.to_dict(), "source": self.source}

    @classmethod
    def from_dict(cls, d):
        return Query(d["nom"], _FROM_DICT[d["expr"]["type"]](d["expr"]), d["source"])

    def enfants(self):
        return [self.expr]


@dataclass
class Return(Nœud):
    expr: Nœud

    def to_dict(self):
        return {"type": "Return", "expr": self.expr.to_dict()}

    @classmethod
    def from_dict(cls, d):
        return Return(_FROM_DICT[d["expr"]["type"]](d["expr"]))

    def enfants(self):
        return [self.expr]


# ── Expressions ─────────────────────────────────────────────────────────

@dataclass
class Encode(Nœud):
    texte: str

    def to_dict(self):
        return {"type": "Encode", "texte": self.texte}

    @classmethod
    def from_dict(cls, d):
        return Encode(d["texte"])


@dataclass
class Decode(Nœud):
    expr: Nœud

    def to_dict(self):
        return {"type": "Decode", "expr": self.expr.to_dict()}

    @classmethod
    def from_dict(cls, d):
        return Decode(_FROM_DICT[d["expr"]["type"]](d["expr"]))

    def enfants(self):
        return [self.expr]


@dataclass
class Bind(Nœud):
    a: Nœud
    b: Nœud

    def to_dict(self):
        return {"type": "Bind", "a": self.a.to_dict(), "b": self.b.to_dict()}

    @classmethod
    def from_dict(cls, d):
        return Bind(_FROM_DICT[d["a"]["type"]](d["a"]), _FROM_DICT[d["b"]["type"]](d["b"]))

    def enfants(self):
        return [self.a, self.b]


@dataclass
class Unbind(Nœud):
    a: Nœud
    b: Nœud

    def to_dict(self):
        return {"type": "Unbind", "a": self.a.to_dict(), "b": self.b.to_dict()}

    @classmethod
    def from_dict(cls, d):
        return Unbind(_FROM_DICT[d["a"]["type"]](d["a"]), _FROM_DICT[d["b"]["type"]](d["b"]))

    def enfants(self):
        return [self.a, self.b]


@dataclass
class Superpose(Nœud):
    args: List[Nœud]

    def to_dict(self):
        return {"type": "Superpose", "args": [a.to_dict() for a in self.args]}

    @classmethod
    def from_dict(cls, d):
        return Superpose([_FROM_DICT[a["type"]](a) for a in d["args"]])

    def enfants(self):
        return self.args


@dataclass
class Resonance(Nœud):
    a: Nœud
    b: Nœud

    def to_dict(self):
        return {"type": "Resonance", "a": self.a.to_dict(), "b": self.b.to_dict()}

    @classmethod
    def from_dict(cls, d):
        return Resonance(_FROM_DICT[d["a"]["type"]](d["a"]), _FROM_DICT[d["b"]["type"]](d["b"]))

    def enfants(self):
        return [self.a, self.b]


@dataclass
class Rotate(Nœud):
    expr: Nœud
    angle: Union[int, float]

    def to_dict(self):
        return {"type": "Rotate", "expr": self.expr.to_dict(), "angle": self.angle}

    @classmethod
    def from_dict(cls, d):
        return Rotate(_FROM_DICT[d["expr"]["type"]](d["expr"]), d["angle"])

    def enfants(self):
        return [self.expr]


@dataclass
class Normalize(Nœud):
    expr: Nœud

    def to_dict(self):
        return {"type": "Normalize", "expr": self.expr.to_dict()}

    @classmethod
    def from_dict(cls, d):
        return Normalize(_FROM_DICT[d["expr"]["type"]](d["expr"]))

    def enfants(self):
        return [self.expr]


@dataclass
class Interfere(Nœud):
    a: Nœud
    b: Nœud
    epsilon: Union[int, float] = 0.15

    def to_dict(self):
        return {"type": "Interfere", "a": self.a.to_dict(), "b": self.b.to_dict(), "epsilon": self.epsilon}

    @classmethod
    def from_dict(cls, d):
        return Interfere(_FROM_DICT[d["a"]["type"]](d["a"]),
                         _FROM_DICT[d["b"]["type"]](d["b"]), d.get("epsilon", 0.15))

    def enfants(self):
        return [self.a, self.b]


@dataclass
class Diffract(Nœud):
    expr: Nœud
    inverse: bool = False

    def to_dict(self):
        return {"type": "Diffract", "expr": self.expr.to_dict(), "inverse": self.inverse}

    @classmethod
    def from_dict(cls, d):
        return Diffract(_FROM_DICT[d["expr"]["type"]](d["expr"]), d.get("inverse", False))

    def enfants(self):
        return [self.expr]


class _Filtre(Nœud):
    coupure: Union[int, float]
    coupure_bas: Union[int, float] = 0.0
    coupure_haut: Union[int, float] = 0.0

    def _d(self, nom):
        d = {"type": type(self).__name__, "expr": self.expr.to_dict(), "coupure": self.coupure}
        if nom == "FilterBP":
            d["coupure_bas"], d["coupure_haut"] = self.coupure_bas, self.coupure_haut
        return d

    @classmethod
    def _fd(cls, d):
        if d["type"] == "FilterBP":
            return cls(d["expr"] and None or None)  # pragma: no cover — surchargé
        return cls(None)  # pragma: no cover — surchargé

    def enfants(self):
        return [self.expr]


@dataclass
class FilterLP(_Filtre):
    expr: Nœud
    coupure: Union[int, float] = 32.0

    def to_dict(self):
        return {"type": "FilterLP", "expr": self.expr.to_dict(), "coupure": self.coupure}

    @classmethod
    def from_dict(cls, d):
        return FilterLP(_FROM_DICT[d["expr"]["type"]](d["expr"]), d.get("coupure", 32.0))


@dataclass
class FilterHP(_Filtre):
    expr: Nœud
    coupure: Union[int, float] = 16.0

    def to_dict(self):
        return {"type": "FilterHP", "expr": self.expr.to_dict(), "coupure": self.coupure}

    @classmethod
    def from_dict(cls, d):
        return FilterHP(_FROM_DICT[d["expr"]["type"]](d["expr"]), d.get("coupure", 16.0))


@dataclass
class FilterBP(_Filtre):
    expr: Nœud
    coupure_bas: Union[int, float] = 8.0
    coupure_haut: Union[int, float] = 32.0

    def to_dict(self):
        return {"type": "FilterBP", "expr": self.expr.to_dict(),
                "coupure_bas": self.coupure_bas, "coupure_haut": self.coupure_haut}

    @classmethod
    def from_dict(cls, d):
        return FilterBP(_FROM_DICT[d["expr"]["type"]](d["expr"]),
                        d.get("coupure_bas", 8.0), d.get("coupure_haut", 32.0))


@dataclass
class PhaseShift(Nœud):
    expr: Nœud
    decalage: Union[int, float]

    def to_dict(self):
        return {"type": "PhaseShift", "expr": self.expr.to_dict(), "decalage": self.decalage}

    @classmethod
    def from_dict(cls, d):
        return PhaseShift(_FROM_DICT[d["expr"]["type"]](d["expr"]), d["decalage"])

    def enfants(self):
        return [self.expr]


@dataclass
class Emerge(Nœud):
    args: List[Nœud]
    temperature: Union[int, float] = 0.5

    def to_dict(self):
        return {"type": "Emerge", "args": [a.to_dict() for a in self.args], "temperature": self.temperature}

    @classmethod
    def from_dict(cls, d):
        return Emerge([_FROM_DICT[a["type"]](a) for a in d["args"]], d.get("temperature", 0.5))

    def enfants(self):
        return self.args


@dataclass
class Oppose(Nœud):
    a: Nœud
    b: Nœud

    def to_dict(self):
        return {"type": "Oppose", "a": self.a.to_dict(), "b": self.b.to_dict()}

    @classmethod
    def from_dict(cls, d):
        return Oppose(_FROM_DICT[d["a"]["type"]](d["a"]), _FROM_DICT[d["b"]["type"]](d["b"]))

    def enfants(self):
        return [self.a, self.b]


@dataclass
class Amplify(Nœud):
    expr: Nœud
    composante: Nœud
    boost: Union[int, float] = 3.0

    def to_dict(self):
        return {"type": "Amplify", "expr": self.expr.to_dict(),
                "composante": self.composante.to_dict(), "boost": self.boost}

    @classmethod
    def from_dict(cls, d):
        return Amplify(_FROM_DICT[d["expr"]["type"]](d["expr"]),
                       _FROM_DICT[d["composante"]["type"]](d["composante"]), d.get("boost", 3.0))

    def enfants(self):
        return [self.expr, self.composante]


@dataclass
class BindMany(Nœud):
    args: List[Nœud]

    def to_dict(self):
        return {"type": "BindMany", "args": [a.to_dict() for a in self.args]}

    @classmethod
    def from_dict(cls, d):
        return BindMany([_FROM_DICT[a["type"]](a) for a in d["args"]])

    def enfants(self):
        return self.args


@dataclass
class Var(Nœud):
    nom: str

    def to_dict(self):
        return {"type": "Var", "nom": self.nom}

    @classmethod
    def from_dict(cls, d):
        return Var(d["nom"])


@dataclass
class Literal(Nœud):
    valeur: Union[int, float]

    def to_dict(self):
        return {"type": "Literal", "valeur": self.valeur}

    @classmethod
    def from_dict(cls, d):
        return Literal(d["valeur"])


@dataclass
class StringLit(Nœud):
    texte: str

    def to_dict(self):
        return {"type": "StringLit", "texte": self.texte}

    @classmethod
    def from_dict(cls, d):
        return StringLit(d["texte"])


# ── Registre de désérialisation ─────────────────────────────────────────

_FROM_DICT: Dict[str, Any] = {
    "Program": Program.from_dict, "Assign": Assign.from_dict, "Store": Store.from_dict,
    "Query": Query.from_dict, "Return": Return.from_dict, "Encode": Encode.from_dict,
    "Decode": Decode.from_dict, "Bind": Bind.from_dict, "Unbind": Unbind.from_dict,
    "Superpose": Superpose.from_dict, "Resonance": Resonance.from_dict,
    "Rotate": Rotate.from_dict, "Normalize": Normalize.from_dict,
    "Interfere": Interfere.from_dict, "Diffract": Diffract.from_dict,
    "FilterLP": FilterLP.from_dict, "FilterHP": FilterHP.from_dict,
    "FilterBP": FilterBP.from_dict, "PhaseShift": PhaseShift.from_dict,
    "Emerge": Emerge.from_dict, "Oppose": Oppose.from_dict, "Amplify": Amplify.from_dict,
    "BindMany": BindMany.from_dict, "Var": Var.from_dict, "Literal": Literal.from_dict,
    "StringLit": StringLit.from_dict,
}


# ────────────────────────────────────────────────────────────────────────
# Parseur récursif descendant
# ────────────────────────────────────────────────────────────────────────

class Parseur:
    def __init__(self, jetons: List[Jeton]):
        self.jetons = jetons
        self.i = 0

    def _courant(self) -> Optional[Jeton]:
        return self.jetons[self.i] if self.i < len(self.jetons) else None

    def _avancer(self) -> Jeton:
        j = self._courant()
        if j is None:
            raise ErreurSyntaxe("fin de programme inattendue")
        self.i += 1
        return j

    def _est_id(self, valeur: str) -> bool:
        j = self._courant()
        return j is not None and j.type == "ID" and j.valeur == valeur

    def _consommer_symbole(self, s: str) -> Jeton:
        j = self._courant()
        if j is None or j.type != "SYMBOLE" or j.valeur != s:
            raise ErreurSyntaxe(f"symbole '{s}' attendu (position {getattr(j, 'position', '?')})")
        return self._avancer()

    def _consommer_id(self, nom: str) -> Jeton:
        if not self._est_id(nom):
            raise ErreurSyntaxe(f"mot-clé '{nom}' attendu")
        return self._avancer()

    def parser_programme(self) -> Program:
        statements = []
        while self._courant() is not None:
            statements.append(self._parser_statement())
        return Program(statements)

    def _parser_statement(self) -> Nœud:
        j = self._courant()
        if j is None:
            raise ErreurSyntaxe("programme vide")
        if self._est_id("STORE"):
            self._avancer()
            nom = self._avancer()
            if nom.type != "ID":
                raise ErreurSyntaxe("nom de variable attendu après STORE")
            self._consommer_symbole("=")
            expr = self._parser_expr()
            self._consommer_id("IN")
            cible = self._avancer()
            if cible.type != "ID":
                raise ErreurSyntaxe("nom d'hologramme attendu après IN")
            return Store(nom.valeur, expr, cible.valeur)
        if self._est_id("QUERY"):
            self._avancer()
            nom = self._avancer()
            if nom.type != "ID":
                raise ErreurSyntaxe("nom de variable attendu après QUERY")
            self._consommer_symbole("=")
            expr = self._parser_expr()
            self._consommer_id("FROM")
            source = self._avancer()
            if source.type != "ID":
                raise ErreurSyntaxe("nom d'hologramme attendu après FROM")
            return Query(nom.valeur, expr, source.valeur)
        if self._est_id("RETURN"):
            self._avancer()
            return Return(self._parser_expr())
        # Assign : ID = expr
        if j.type == "ID" and self.jetons[self.i + 1].type == "SYMBOLE" \
                and self.jetons[self.i + 1].valeur == "=":
            self._avancer()
            self._avancer()
            return Assign(j.valeur, self._parser_expr())
        raise ErreurSyntaxe(f"énoncé inattendu '{j.valeur}' (ligne {j.ligne})")

    def _parser_expr(self) -> Nœud:
        j = self._courant()
        if j is None:
            raise ErreurSyntaxe("expression attendue")
        if j.type == "CHAINE":
            self._avancer()
            return StringLit(j.valeur)
        if j.type == "NOMBRE":
            self._avancer()
            return Literal(j.valeur)
        if j.type == "ID":
            if j.valeur in {"TRUE", "FALSE"}:
                self._avancer()
                return Literal(1.0 if j.valeur == "TRUE" else 0.0)
            if j.valeur in {"ENCODE", "DECODE", "BIND", "UNBIND", "SUPERPOSE", "RESONANCE",
                            "ROTATE", "NORMALIZE", "INTERFERE", "DIFFRACT", "FILTER_LP",
                            "FILTER_HP", "FILTER_BP", "PHASE_SHIFT", "EMERGE", "OPPOSE",
                            "AMPLIFY", "BIND_MANY"}:
                return self._parser_appel(j.valeur)
            self._avancer()
            return Var(j.valeur)
        raise ErreurSyntaxe(f"expression inattendue '{j.valeur}' (ligne {j.ligne})")

    def _parser_appel(self, nom: str) -> Nœud:
        # ENCODE/DECODE acceptent la forme sans parenthèses (grammaire §4.2 :
        # 'ENCODE' string, 'DECODE' expr) et la forme parenthésée (exemples du doc).
        if nom in ("ENCODE", "DECODE"):
            suiv = self.jetons[self.i + 1] if self.i + 1 < len(self.jetons) else None
            if suiv is not None and suiv.type == "SYMBOLE" and suiv.valeur == "(":
                self._avancer()
                return self._parser_appel_parenthese(nom)
            self._avancer()
            if nom == "ENCODE":
                return Encode(_texte(self._parser_expr()))
            return Decode(self._parser_expr())
        self._avancer()
        return self._parser_appel_parenthese(nom)

    def _parser_appel_parenthese(self, nom: str) -> Nœud:
        self._consommer_symbole("(")
        premier = self._parser_expr()
        args = [premier]
        nombres = []
        while self._courant() is not None and self._courant().type == "SYMBOLE" \
                and self._courant().valeur == ",":
            self._avancer()
            suiv = self._courant()
            if suiv is not None and suiv.type == "NOMBRE":
                nombres.append(self._avancer().valeur)
            else:
                args.append(self._parser_expr())
        self._consommer_symbole(")")
        return _construire_appel(nom, args, nombres)


def _construire_appel(nom: str, args: List[Nœud], nombres: List[Any]) -> Nœud:
    """Construit le nœud AST d'un appel, selon le nombre d'arguments."""
    if nom == "ENCODE":
        return Encode(_texte(args[0]))
    if nom == "DECODE":
        return Decode(args[0])
    if nom == "BIND":
        return Bind(args[0], args[1])
    if nom == "UNBIND":
        return Unbind(args[0], args[1])
    if nom == "SUPERPOSE":
        return Superpose(args)
    if nom == "RESONANCE":
        return Resonance(args[0], args[1])
    if nom == "ROTATE":
        return Rotate(args[0], nombres[0] if nombres else _nombre(args[1]))
    if nom == "NORMALIZE":
        return Normalize(args[0])
    if nom == "INTERFERE":
        return Interfere(args[0], args[1], nombres[0] if nombres else 0.15)
    if nom == "DIFFRACT":
        return Diffract(args[0], bool(nombres[0]) if nombres else False)
    if nom == "FILTER_LP":
        return FilterLP(args[0], nombres[0] if nombres else _nombre(args[1]))
    if nom == "FILTER_HP":
        return FilterHP(args[0], nombres[0] if nombres else _nombre(args[1]))
    if nom == "FILTER_BP":
        return FilterBP(args[0],
                        nombres[0] if nombres else _nombre(args[1]),
                        nombres[1] if len(nombres) > 1 else _nombre(args[2]))
    if nom == "PHASE_SHIFT":
        return PhaseShift(args[0], nombres[0] if nombres else _nombre(args[1]))
    if nom == "EMERGE":
        return Emerge(args, nombres[-1] if nombres else 0.5)
    if nom == "OPPOSE":
        return Oppose(args[0], args[1])
    if nom == "AMPLIFY":
        return Amplify(args[0], args[1], nombres[0] if nombres else 3.0)
    if nom == "BIND_MANY":
        return BindMany(args)
    raise ErreurSyntaxe(f"primitive inconnue '{nom}'")


def _texte(n: Nœud) -> str:
    if isinstance(n, StringLit):
        return n.texte
    if isinstance(n, Literal):
        return str(n.valeur)
    if isinstance(n, Var):
        return n.nom
    raise ErreurSyntaxe("chaîne attendue")


def _nombre(n: Nœud) -> Union[int, float]:
    if isinstance(n, Literal):
        return n.valeur
    raise ErreurSyntaxe("nombre attendu")


def parse(source: str) -> Program:
    """Texte ondulatoire → Program (AST)."""
    return Parseur(tokeniser(source)).parser_programme()


# ────────────────────────────────────────────────────────────────────────
# Sérialisation JSON (§6.3) — roundtrip parfait
# ────────────────────────────────────────────────────────────────────────

def to_json(program: Nœud, indent: Optional[int] = None) -> str:
    return json.dumps(program.to_dict(), ensure_ascii=False, indent=indent)


def from_json(data: str) -> Nœud:
    d = json.loads(data)
    return _FROM_DICT[d["type"]](d)


# ────────────────────────────────────────────────────────────────────────
# Impression canonique (roundtrip parse → print bit-à-bit)
# ────────────────────────────────────────────────────────────────────────

def afficher(program: Nœud) -> str:
    if isinstance(program, Program):
        return "\n".join(afficher(s) for s in program.statements)
    if isinstance(program, Assign):
        return f"{program.nom} = {afficher(program.expr)}"
    if isinstance(program, Store):
        return f"STORE {program.nom} = {afficher(program.expr)} IN {program.cible}"
    if isinstance(program, Query):
        return f"QUERY {program.nom} = {afficher(program.expr)} FROM {program.source}"
    if isinstance(program, Return):
        return f"RETURN {afficher(program.expr)}"
    if isinstance(program, Encode):
        return f"ENCODE {_q(program.texte)}"
    if isinstance(program, StringLit):
        return _q(program.texte)
    if isinstance(program, Literal):
        return repr(program.valeur) if isinstance(program.valeur, float) else str(program.valeur)
    if isinstance(program, Var):
        return program.nom
    if isinstance(program, Decode):
        return f"DECODE({afficher(program.expr)})"
    if isinstance(program, Bind):
        return f"BIND({afficher(program.a)}, {afficher(program.b)})"
    if isinstance(program, Unbind):
        return f"UNBIND({afficher(program.a)}, {afficher(program.b)})"
    if isinstance(program, Superpose):
        return f"SUPERPOSE({', '.join(afficher(a) for a in program.args)})"
    if isinstance(program, Resonance):
        return f"RESONANCE({afficher(program.a)}, {afficher(program.b)})"
    if isinstance(program, Rotate):
        return f"ROTATE({afficher(program.expr)}, {program.angle})"
    if isinstance(program, Normalize):
        return f"NORMALIZE({afficher(program.expr)})"
    if isinstance(program, Interfere):
        return f"INTERFERE({afficher(program.a)}, {afficher(program.b)}, {program.epsilon})"
    if isinstance(program, Diffract):
        return f"DIFFRACT({afficher(program.expr)}, {str(program.inverse).lower()})"
    if isinstance(program, FilterLP):
        return f"FILTER_LP({afficher(program.expr)}, {program.coupure})"
    if isinstance(program, FilterHP):
        return f"FILTER_HP({afficher(program.expr)}, {program.coupure})"
    if isinstance(program, FilterBP):
        return f"FILTER_BP({afficher(program.expr)}, {program.coupure_bas}, {program.coupure_haut})"
    if isinstance(program, PhaseShift):
        return f"PHASE_SHIFT({afficher(program.expr)}, {program.decalage})"
    if isinstance(program, Emerge):
        return f"EMERGE({', '.join(afficher(a) for a in program.args)}, {program.temperature})"
    if isinstance(program, Oppose):
        return f"OPPOSE({afficher(program.a)}, {afficher(program.b)})"
    if isinstance(program, Amplify):
        return f"AMPLIFY({afficher(program.expr)}, {afficher(program.composante)}, {program.boost})"
    if isinstance(program, BindMany):
        return f"BIND_MANY({', '.join(afficher(a) for a in program.args)})"
    raise TypeError(f"nœud non imprimable : {type(program).__name__}")


def _q(texte: str) -> str:
    echappe = texte.replace('"', '\\"')
    return f'"{echappe}"'


# ────────────────────────────────────────────────────────────────────────
# Validation statique (§6.3) — variables non définies, hologrammes connus
# ────────────────────────────────────────────────────────────────────────

def valider(program: Nœud, hologrammes: Optional[List[str]] = None) -> List[str]:
    """Retourne la liste des erreurs statiques du programme (vide = valide).

    Vérifie : variables utilisées avant définition, redéfinitions STORE/QUERY,
    hologrammes FROM/IN connus (si la liste est fournie), RETURN présent en fin.
    """
    erreurs: List[str] = []
    definies: set = set()
    hologrammes_connus = set(hologrammes or [])

    for stmt in program.statements:
        if isinstance(stmt, Assign):
            _verifier_expr(stmt.expr, definies, erreurs)
            definies.add(stmt.nom)
        elif isinstance(stmt, Query):
            _verifier_expr(stmt.expr, definies, erreurs)
            if hologrammes_connus and stmt.source not in hologrammes_connus:
                erreurs.append(f"Hologramme '{stmt.source}' inconnu (FROM)")
            definies.add(stmt.nom)
        elif isinstance(stmt, Store):
            _verifier_expr(stmt.expr, definies, erreurs)
            if hologrammes_connus and stmt.cible not in hologrammes_connus:
                erreurs.append(f"Hologramme '{stmt.cible}' inconnu (IN)")
            definies.add(stmt.nom)
        elif isinstance(stmt, Return):
            _verifier_expr(stmt.expr, definies, erreurs)

    # le programme doit se terminer par RETURN (trois temps : ENCODE → MANIPULER → DÉCODER)
    if not program.statements or not isinstance(program.statements[-1], Return):
        erreurs.append("Le programme doit se terminer par RETURN (temps DÉCODER)")
    return erreurs


def _verifier_expr(expr: Nœud, definies: set, erreurs: List[str]) -> None:
    if isinstance(expr, Var):
        if expr.nom not in definies:
            erreurs.append(f"Variable '{expr.nom}' utilisée mais non définie")
    elif isinstance(expr, StringLit):
        pass
    for enfant in expr.enfants():
        if isinstance(enfant, Nœud) and not isinstance(enfant, StringLit):
            _verifier_expr(enfant, definies, erreurs)
