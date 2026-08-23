# -*- coding: utf-8 -*-
"""
moteur.py — Le compilateur/exécuteur ondulatoire.

Conforme au DOCUMENT_FONDATEUR_LANGAGE_ONDULATOIRE.md §7 (compilateur : passes
d'optimisation) et §4.3 (exécution du programme canonique). L'interpréteur
exécute un Program (AST du wave IR) contre des hologrammes, dans le respect de
la sémantique des primitives :

    RESONANCE → scalaire normalisé ∈ [-1, 1]
    QUERY     → résulte en un QueryResult (faits résonants + onde agrégée)
    DECODE    → entité(s) du vocabulaire ou faits du QueryResult
    RETURN    → env['__return__'] (le programme se termine par DÉCODER)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

import ir
from primitives import (DEFAULT_DIM, Fait, HolographicMemory, Wave, amplify,
                        bind, bind_many, decode, diffract, emerge, encode,
                        filter_wave, interfere, normalize, oppose, phase_shift,
                        resonate, rotate, superpose, unbind)

Valeur = Union[Wave, float, str, "QueryResult"]


@dataclass
class QueryResult:
    """Résultat d'un QUERY : les faits résonants et l'onde qu'ils émergent."""
    faits: List[Tuple[Fait, float]] = field(default_factory=list)
    source: str = ""

    @property
    def psi(self) -> Wave:
        """L'onde agrégée des faits gagnants (interférence de la réponse)."""
        if not self.faits:
            return np.zeros(DEFAULT_DIM, dtype=np.complex128)
        return superpose(*[f.psi for f, _ in self.faits])

    @property
    def meilleur_score(self) -> float:
        return self.faits[0][1] if self.faits else 0.0

    def textes(self) -> List[str]:
        return [f.texte() for f, _ in self.faits]


class ErreurExecution(Exception):
    """Erreur d'exécution d'un programme ondulatoire."""


class MoteurOndulatoire:
    """Interpréteur + passes d'optimisation du langage ondulatoire."""

    def __init__(self, dim: int = DEFAULT_DIM):
        self.dim = dim

    # ── optimisation (§7.1) ─────────────────────────────────────────────
    def optimiser(self, programme: ir.Program) -> Tuple[ir.Program, Dict[str, int]]:
        """Passes 1-2 : constant folding (report) + dead code elimination."""
        stats = {"constantes_pliees": 0, "codes_morts": 0}

        # Pass 1 — constant folding : les ENCODE de chaînes identiques sont uniques
        encode_par_texte: Dict[str, ir.Nœud] = {}
        for stmt in programme.statements:
            _pliage(stmt, encode_par_texte, stats)

        # Pass 2 — dead code elimination : supprime les Assign jamais utilisés
        utilises: set = set()
        for stmt in programme.statements:
            _marquer_utilises(stmt, utilises)
        gardes = []
        for stmt in programme.statements:
            if isinstance(stmt, ir.Assign) and stmt.nom not in utilises:
                stats["codes_morts"] += 1
                continue
            gardes.append(stmt)
        return ir.Program(gardes), stats

    def compiler(self, programme: ir.Program) -> Dict[str, Any]:
        """Compile : optimise, émet du code Python équivalent et mesure les stats."""
        optimise, stats = self.optimiser(programme)
        return {
            "programme": optimise,
            "stats": stats,
            "python_code": self._emettre_python(optimise),
            "lignes_python": len(self._emettre_python(optimise).splitlines()),
        }

    def _emettre_python(self, programme: ir.Program) -> str:
        lignes = []
        for stmt in programme.statements:
            if isinstance(stmt, ir.Assign):
                lignes.append(f"{stmt.nom} = {_expr_python(stmt.expr)}")
            elif isinstance(stmt, ir.Query):
                lignes.append(f"{stmt.nom} = {stmt.source}.interroger({_expr_python(stmt.expr)})")
            elif isinstance(stmt, ir.Store):
                lignes.append(f"{stmt.cible}.store_psi({_expr_python(stmt.expr)}, '')")
            elif isinstance(stmt, ir.Return):
                lignes.append(f"__retour__ = {_expr_python(stmt.expr)}")
        return "\n".join(lignes)

    # ── exécution ───────────────────────────────────────────────────────
    def executer(self, programme: ir.Program, hologrammes: Optional[Dict[str, HolographicMemory]] = None,
                 vocabulaire: Optional[Dict[str, Wave]] = None) -> Dict[str, Any]:
        """Exécute un programme ondulatoire ; retourne l'environnement final.

        hologrammes : {nom: HolographicMemory} — cibles de QUERY/STORE.
        vocabulaire  : {mot: ψ} — monde de décodage de DECODE.
        """
        hologrammes = hologrammes or {}
        vocabulaire = vocabulaire or {}
        env: Dict[str, Any] = {}
        self._textes_faits: Dict[str, tuple] = {}
        self._chaine_var: Dict[str, str] = {}

        for stmt in programme.statements:
            if isinstance(stmt, ir.Assign):
                env[stmt.nom] = self._evaluer(stmt.expr, env, hologrammes, vocabulaire)
                if isinstance(stmt.expr, ir.Encode):
                    self._chaine_var[stmt.nom] = stmt.expr.texte
                triple = self._triplet_expr(stmt.expr)
                if triple:
                    self._textes_faits[stmt.nom] = triple   # texte du fait lié
            elif isinstance(stmt, ir.Query):
                psi_q = self._evaluer(stmt.expr, env, hologrammes, vocabulaire)
                holo = self._hologramme(stmt.source, hologrammes, env)
                faits = holo.interroger(self._onde(psi_q), top_k=12, seuil=0.0)
                # QUERY étendu : les mots pleins de la question résonnent aussi
                # (la question est un paquet de concepts — §5.2.6 retrieval top-k)
                texte_question = None
                if isinstance(stmt.expr, ir.Encode):
                    texte_question = stmt.expr.texte
                elif isinstance(stmt.expr, ir.Var):
                    texte_question = self._chaine_var.get(stmt.expr.nom)
                if texte_question:
                    faits = self._query_etendu(holo, texte_question, faits)
                faits = [t for t in faits if t[1] > 0.02][:8]
                env[stmt.nom] = QueryResult(faits=faits, source=stmt.source)
            elif isinstance(stmt, ir.Store):
                psi_f = self._evaluer(stmt.expr, env, hologrammes, vocabulaire)
                holo = self._hologramme(stmt.cible, hologrammes, env)
                triple = self._triplet_expr(stmt.expr)
                if triple is None and isinstance(stmt.expr, ir.Var):
                    triple = self._textes_faits.get(stmt.expr.nom)
                if triple is not None:
                    holo.store(*triple)                    # fait texte (récupérable)
                    env[stmt.nom] = triple
                else:
                    holo.store_psi(self._onde(psi_f), "fait émergent")
                    env[stmt.nom] = psi_f
            elif isinstance(stmt, ir.Return):
                env["__return__"] = self._evaluer(stmt.expr, env, hologrammes, vocabulaire)
        return env

    # ── évaluation ──────────────────────────────────────────────────────
    def _evaluer(self, expr: ir.Nœud, env: Dict[str, Any],
                 hologrammes: Dict[str, HolographicMemory],
                 vocabulaire: Dict[str, Wave]) -> Valeur:
        if isinstance(expr, ir.Literal):
            return float(expr.valeur)
        if isinstance(expr, ir.StringLit):
            return expr.texte
        if isinstance(expr, ir.Var):
            if expr.nom in env:
                return env[expr.nom]
            if expr.nom in hologrammes:                     # l'hologramme lui-même
                return hologrammes[expr.nom]
            raise ErreurExecution(f"Variable '{expr.nom}' non définie")
        if isinstance(expr, ir.Encode):
            return encode(expr.texte, self.dim)
        if isinstance(expr, ir.Decode):
            valeur = self._evaluer(expr.expr, env, hologrammes, vocabulaire)
            return self._decoder(valeur, vocabulaire)
        if isinstance(expr, ir.Bind):
            return bind(self._onde(self._evaluer(expr.a, env, hologrammes, vocabulaire)),
                        self._onde(self._evaluer(expr.b, env, hologrammes, vocabulaire)))
        if isinstance(expr, ir.Unbind):
            return unbind(self._onde(self._evaluer(expr.a, env, hologrammes, vocabulaire)),
                          self._onde(self._evaluer(expr.b, env, hologrammes, vocabulaire)))
        if isinstance(expr, ir.Superpose):
            return superpose(*[self._onde(self._evaluer(a, env, hologrammes, vocabulaire))
                               for a in expr.args])
        if isinstance(expr, ir.Resonance):
            a = self._evaluer(expr.a, env, hologrammes, vocabulaire)
            b = self._evaluer(expr.b, env, hologrammes, vocabulaire)
            if isinstance(a, HolographicMemory):
                a = self._onde(a)                           # mémoire entière → onde
            if isinstance(b, HolographicMemory):
                b = self._onde(b)
            return float(resonate(self._onde(a), self._onde(b)))
        if isinstance(expr, ir.Rotate):
            return rotate(self._onde(self._evaluer(expr.expr, env, hologrammes, vocabulaire)),
                          float(expr.angle))
        if isinstance(expr, ir.Normalize):
            return normalize(self._onde(self._evaluer(expr.expr, env, hologrammes, vocabulaire)))
        if isinstance(expr, ir.Interfere):
            return interfere(self._onde(self._evaluer(expr.a, env, hologrammes, vocabulaire)),
                             self._onde(self._evaluer(expr.b, env, hologrammes, vocabulaire)),
                             float(expr.epsilon))
        if isinstance(expr, ir.Diffract):
            return diffract(self._onde(self._evaluer(expr.expr, env, hologrammes, vocabulaire)),
                            inverse=bool(expr.inverse))
        if isinstance(expr, ir.FilterLP):
            return filter_wave(self._onde(self._evaluer(expr.expr, env, hologrammes, vocabulaire)),
                               "low", float(expr.coupure))
        if isinstance(expr, ir.FilterHP):
            return filter_wave(self._onde(self._evaluer(expr.expr, env, hologrammes, vocabulaire)),
                               "high", float(expr.coupure))
        if isinstance(expr, ir.FilterBP):
            return filter_wave(self._onde(self._evaluer(expr.expr, env, hologrammes, vocabulaire)),
                               "band", cutoff_bas=float(expr.coupure_bas),
                               cutoff_haut=float(expr.coupure_haut))
        if isinstance(expr, ir.PhaseShift):
            return phase_shift(self._onde(self._evaluer(expr.expr, env, hologrammes, vocabulaire)),
                               float(expr.decalage))
        if isinstance(expr, ir.Emerge):
            return emerge(*[self._onde(self._evaluer(a, env, hologrammes, vocabulaire))
                            for a in expr.args], temperature=float(expr.temperature))
        if isinstance(expr, ir.Oppose):
            return oppose(self._onde(self._evaluer(expr.a, env, hologrammes, vocabulaire)),
                          self._onde(self._evaluer(expr.b, env, hologrammes, vocabulaire)))
        if isinstance(expr, ir.Amplify):
            return amplify(self._onde(self._evaluer(expr.expr, env, hologrammes, vocabulaire)),
                           self._onde(self._evaluer(expr.composante, env, hologrammes, vocabulaire)),
                           float(expr.boost))
        if isinstance(expr, ir.BindMany):
            return bind_many(*[self._onde(self._evaluer(a, env, hologrammes, vocabulaire))
                               for a in expr.args])
        raise ErreurExecution(f"Expression inconnue : {type(expr).__name__}")

    # ── aide ────────────────────────────────────────────────────────────
    def _triplet_expr(self, expr: ir.Nœud) -> Optional[Tuple[str, str, str]]:
        """Triplet (sujet, relation, objet) d'un BIND_MANY d'ENCodes (via variables)."""
        if not isinstance(expr, ir.BindMany) or len(expr.args) < 3:
            return None
        textes = [self._texte_arg(a) for a in expr.args[:3]]
        if all(t is not None for t in textes):
            return tuple(textes)  # type: ignore
        return None

    def _texte_arg(self, arg: ir.Nœud) -> Optional[str]:
        if isinstance(arg, ir.Encode):
            return arg.texte
        if isinstance(arg, ir.Var):
            return self._chaine_var.get(arg.nom)
        return None

    def _query_etendu(self, holo: HolographicMemory, texte: str,
                      faits_existants: List[Tuple[Fait, float]]) -> List[Tuple[Fait, float]]:
        """Complète un QUERY : superposition des mots pleins + bonus lexical.

        seuil = -1.0 : aucun fait n'est écarté d'emblée — le bonus lexical doit
        pouvoir sauver un fait dont la résonance seule est négative (bruit).
        Le bonus s'applique aussi aux faits déjà retenus par la résonance."""
        from generateur import _pseudo_mots
        mots = _pseudo_mots(texte)[:6]
        if not mots:
            return faits_existants
        psi_mots = superpose(*[encode(m, self.dim) for m in mots])
        extra = holo.interroger(psi_mots, top_k=1000, seuil=-1.0)

        def bonus(fait: Fait) -> float:
            texte_fait = f"{fait.sujet} {fait.relation} {fait.objet}".lower()
            return 0.18 * sum(1 for m in mots if m in texte_fait)

        resultats = {id(f): (f, s) for f, s in faits_existants}
        for fait, score in extra:
            total = max(score, 0.0) + bonus(fait)
            if id(fait) in resultats:
                _, ancien = resultats[id(fait)]
                resultats[id(fait)] = (fait, max(ancien, total))
            else:
                resultats[id(fait)] = (fait, total)
        faits = sorted(resultats.values(), key=lambda t: -t[1])
        return faits[:8]

    def _onde(self, valeur: Valeur) -> Wave:
        if isinstance(valeur, QueryResult):
            return valeur.psi
        if isinstance(valeur, HolographicMemory):
            return normalize(valeur._memoire)
        if isinstance(valeur, np.ndarray):
            return valeur
        if isinstance(valeur, str):
            return encode(valeur, self.dim)
        raise ErreurExecution(f"Impossible d'utiliser {type(valeur).__name__} comme onde")

    def _hologramme(self, nom: str, hologrammes: Dict[str, HolographicMemory], env) -> HolographicMemory:
        if nom in hologrammes:
            return hologrammes[nom]
        if nom in env and isinstance(env[nom], HolographicMemory):
            return env[nom]
        raise ErreurExecution(f"Hologramme '{nom}' inconnu")

    def _decoder(self, valeur: Valeur, vocabulaire: Dict[str, Wave]):
        """DÉCODER : entité → monde. QueryResult → faits ; onde → plus proche voisin."""
        if isinstance(valeur, QueryResult):
            return [f.texte() for f, _ in valeur.faits]
        if isinstance(valeur, str):
            return valeur
        if isinstance(valeur, np.ndarray):
            mots = decode(valeur, vocabulaire, top_k=5)
            return [mot for mot, _ in mots]
        if isinstance(valeur, (int, float)):
            return []
        return []


# ────────────────────────────────────────────────────────────────────────
# Passes d'optimisation — aide
# ────────────────────────────────────────────────────────────────────────

def _pliage(noeud: ir.Nœud, cache: Dict[str, ir.Nœud], stats: Dict[str, int]) -> None:
    """Compte les ENCODE redondants (candidats au folding)."""
    if isinstance(noeud, ir.Encode):
        if noeud.texte in cache:
            stats["constantes_pliees"] += 1
        else:
            cache[noeud.texte] = noeud
    for enfant in noeud.enfants():
        _pliage(enfant, cache, stats)


def _marquer_utilises(noeud: ir.Nœud, utilises: set) -> None:
    if isinstance(noeud, ir.Var):
        utilises.add(noeud.nom)
    for enfant in noeud.enfants():
        _marquer_utilises(enfant, utilises)


def _triplet_encode(expr: ir.Nœud) -> Optional[Tuple[str, str, str]]:
    """Si l'expression est BIND_MANY(ENCODE s, ENCODE r, ENCODE o) → (s, r, o)."""
    if not isinstance(expr, ir.BindMany) or len(expr.args) < 3:
        return None
    textes = []
    for arg in expr.args:
        if not isinstance(arg, ir.Encode):
            return None
        textes.append(arg.texte)
    return tuple(textes[:3])  # type: ignore


def _expr_python(expr: ir.Nœud) -> str:
    if isinstance(expr, ir.Encode):
        return f"encode({expr.texte!r})"
    if isinstance(expr, ir.StringLit):
        return repr(expr.texte)
    if isinstance(expr, ir.Literal):
        return repr(expr.valeur)
    if isinstance(expr, ir.Var):
        return expr.nom
    nom = type(expr).__name__.lower()
    return f"{nom}({', '.join(_expr_python(e) for e in expr.enfants())})"
