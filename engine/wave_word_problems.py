"""
🌊 Wave Word Problems — Moteur de problèmes multi-étapes
==========================================================

Les problèmes de mots (style GSM8K) : énoncé → étapes → programme
harmonique → exécution → résultat + étapes documentées.

Chaque étape est un MathOp ; le programme harmonique final est exécuté
par WaveCompiler (double preuve : interpréteur + code converti).

Patterns couverts :
  - Achats : « X objets à Y € chacun », « X à Y € et Z à W € »
  - Vitesse : « V km/h pendant T heures/minutes »
  - Règle de trois : « X ouvriers font Y murs en Z jours, W ouvriers ? »
  - Nénuphar : « double chaque jour, couvre en N jours, quand la moitié ? »
  - Poignées de main : « N personnes se serrent la main »
  - Secondes : « combien de secondes dans X heures »
  - Partages : « X partagé entre Y personnes »
  - Enchaînés : « X plus Y fois Z » (priorités)

Usage :
    from wave_word_problems import WaveWordProblemEngine

    engine = WaveWordProblemEngine()
    r = engine.solve("Un train roule à 100 km/h pendant 2h30. Quelle distance ?")
    print(r.result)    # 250.0
    print(r.steps)     # ['2h30 → 2.5 heures', '100 × 2.5 = 250']
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Callable

from wave_ir import Program, Assign, Return, MathOp, Literal, Var
from wave_compiler import WaveCompiler
from wave_emit import emit_python


# ═══════════════════════════════════════════════════════════════════════════════
# RÉSULTAT
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class WordProblemResult:
    """Résultat d'un problème multi-étapes."""
    result: float
    steps: List[str] = field(default_factory=list)
    expression: str = ""          # syntaxe harmonique du calcul
    question: str = ""
    method: str = ""

    @property
    def is_valid(self) -> bool:
        return self.result is not None


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _num(s: str) -> float:
    """Convertit un texte numérique (virgule décimale OU milliers)."""
    s = s.strip()
    # "80,000" → milliers (3 chiffres après la virgule)
    if ',' in s and re.fullmatch(r'\d+,\d{3}(?:\.\d+)?', s):
        s = s.replace(',', '')
    else:
        s = s.replace(',', '.')
    return float(s)


# Nombres en lettres (anglais + français) — pour GSM8K
_WORD_NUMBERS = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14,
    'fifteen': 15, 'sixteen': 16, 'seventeen': 17, 'eighteen': 18,
    'nineteen': 19, 'twenty': 20, 'thirty': 30, 'forty': 40,
    'fifty': 50, 'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90,
    'hundred': 100, 'thousand': 1000, 'dozen': 12, 'couple': 2,
    # 'un'/'une' exclus : articles trop fréquents ("un train", "un nénuphar")
    'zero': 0, 'deux': 2, 'trois': 3, 'quatre': 4,
    'cinq': 5, 'six': 6, 'sept': 7, 'huit': 8, 'neuf': 9, 'dix': 10,
    'onze': 11, 'douze': 12, 'treize': 13, 'quatorze': 14, 'quinze': 15,
    'seize': 16, 'vingt': 20, 'trente': 30, 'quarante': 40, 'cinquante': 50,
    'soixante': 60, 'cent': 100, 'mille': 1000,
}


def _normalize_numbers(q: str) -> str:
    """Remplace les nombres en lettres par des chiffres (frontières de mots)."""
    for word, num in sorted(_WORD_NUMBERS.items(), key=lambda x: -len(x[0])):
        q = re.sub(rf'\b{word}\b', str(num), q)
    return q


def _fmt(n: float) -> str:
    """Formate un nombre sans .0 inutile."""
    return str(int(n)) if float(n).is_integer() else str(round(n, 4))


def _lit(n: float) -> Literal:
    return Literal(float(n))


def _fmt_time(hours: float) -> str:
    """2.5 → '2h30'."""
    h = int(hours)
    m = int(round((hours - h) * 60))
    if m == 0:
        return f"{h}h"
    return f"{h}h{m:02d}"


# ═══════════════════════════════════════════════════════════════════════════════
# LE MOTEUR
# ═══════════════════════════════════════════════════════════════════════════════

class WaveWordProblemEngine:
    """
    Résout les problèmes de mots multi-étapes.

    Chaque détecteur retourne (steps, expr, method) où expr est un
    MathOp AST ; le programme final est exécuté par WaveCompiler.
    """

    def __init__(self, dim: int = 64):
        self.dim = dim
        self._compiler = WaveCompiler(dim=dim)

    def solve(self, question: str) -> Optional[WordProblemResult]:
        """
        Résout un problème multi-étapes.

        Returns:
            WordProblemResult ou None si aucun pattern ne matche
        """
        q = question.lower().strip().rstrip('?')
        # Normaliser les nombres en lettres (GSM8K : "three", "twelve"...)
        q = _normalize_numbers(q)

        detectors: List[Tuple[str, Callable[[str], Optional[Tuple[List[str], MathOp]]]]] = [
            ("nénuphar", self._solve_nenuphar),
            ("poignées de main", self._solve_handshakes),
            ("règle de trois", self._solve_rule_of_three),
            ("production/consommation", self._solve_production),
            ("moitiés/multiples", self._solve_halves),
            ("profit", self._solve_profit),
            ("reste", self._solve_remaining),
            ("vitesse", self._solve_speed),
            ("secondes", self._solve_seconds),
            ("achats combinés", self._solve_two_purchases),
            ("achat", self._solve_purchase),
            ("partage", self._solve_share),
            ("augmentation", self._solve_increase),
            ("réduction", self._solve_discount),
        ]

        for method, detector in detectors:
            try:
                found = detector(q)
            except Exception:
                continue
            if found is None:
                continue
            steps, expr = found

            # Exécution (interpréteur harmonique)
            prog = Program([
                Assign("resultat", expr),
                Return(Var("resultat")),
            ])
            env = self._compiler.execute(prog)
            result = env.get("resultat")
            if result is None:
                continue

            steps.append(f"→ résultat : {_fmt(float(result))}")
            return WordProblemResult(
                result=float(result),
                steps=steps,
                expression=prog.to_wave(),
                question=question,
                method=method,
            )

        # Fallback : CONSENSUS MULTI-PLANS (l'équivalent ondulatoire du
        # majority voting LLM) — état séquentiel + motifs composés + formule
        # directe ; convergence de 2 stratégies → résultat adopté
        try:
            from word_problem_state import solve_consensus
            res = solve_consensus(question)
            if res is not None:
                result, steps = res
                return WordProblemResult(
                    result=float(result),
                    steps=steps,
                    expression='',
                    question=question,
                    method='consensus',
                )
        except Exception:
            pass

        # Fallback : expression arithmétique directe (enchaînés)
        try:
            from wave_code_generator import WaveCodeGenerator
            gen = WaveCodeGenerator()
            expr = gen._parse_math_expr(question)
            if expr is not None:
                prog = Program([
                    Assign("resultat", expr),
                    Return(Var("resultat")),
                ])
                env = self._compiler.execute(prog)
                result = env.get("resultat")
                if result is not None:
                    return WordProblemResult(
                        result=float(result),
                        steps=[f"expression : {prog.to_wave()}"],
                        expression=prog.to_wave(),
                        question=question,
                        method="enchaîné",
                    )
        except Exception:
            pass
        return None

    # ── Détecteurs ─────────────────────────────────────────────────────────

    def _solve_purchase(self, q: str) -> Optional[Tuple[List[str], MathOp]]:
        """« X objets à Y € chacun » / "X items at Y dollars each" → X×Y."""
        m = re.search(r'(\d+)\s+(?:objets?|pommes?|livres?|stylos?|bouteilles?|'
                      r'baguettes?|cahiers?|billets?|vélos?|places?|'
                      r'items?|apples?|books?|shirts?|tickets?)\s+(?:à|at)\s+'
                      r'(\d+(?:[.,]\d+)?)\s*(?:euros?|€|francs?|dollars?|'
                      r'\$|pounds?|€)?', q)
        if not m:
            return None
        n_items, price = int(m.group(1)), _num(m.group(2))
        expr = MathOp('MUL', _lit(n_items), _lit(price))
        return ([f"{n_items} × {_fmt(price)} = {_fmt(n_items * price)}"],
                expr)

    def _solve_production(self, q: str) -> Optional[Tuple[List[str], MathOp]]:
        """« X per day, Y used per day, how many left after Z days? »
           / « produit X par jour, consomme Y, reste après Z jours ? »"""
        # Production - consommation par unité de temps × durée
        m = re.search(r'(\d+)\s+(?:per|par)\s+(day|week|jour|semaine).*?'
                      r'(?:eats|uses|consumes|mange|consomme)\s+(\d+).*?'
                      r'(?:how many|combien).*?(?:left|rest|reste|needed).*?'
                      r'(\d+)\s*(?:days?|weeks?|jours?|semaines?)?', q)
        if not m:
            return None
        produced, consumed = int(m.group(1)), int(m.group(3))
        periods = int(m.group(4)) if m.group(4) else 1
        net = produced - consumed
        expr = MathOp('MUL', _lit(net), _lit(periods))
        return ([f"{produced} − {consumed} = {net} par période",
                 f"{net} × {periods} = {net * periods}"], expr)

    def _solve_halves(self, q: str) -> Optional[Tuple[List[str], MathOp]]:
        """« X and half that much Y, how many in total? »
           / « X et la moitié de Y, total ? »"""
        m = re.search(r'(\d+(?:[.,]\d+)?)\s+.*?'
                      r'\b(?:and|et)\s+(?:half that much|half as much|half|'
                      r'la moitié)\b.*?(?:in total|au total|total)?', q)
        if not m:
            return None
        base = _num(m.group(1))
        expr = MathOp('ADD', _lit(base), MathOp('DIV', _lit(base), _lit(2.0)))
        return ([f"{_fmt(base)} + {_fmt(base)}/2 = {_fmt(base + base / 2)}"],
                expr)

    def _solve_profit(self, q: str) -> Optional[Tuple[List[str], MathOp]]:
        """« buys for X, puts in Y, sells for Z, profit? »
           / « achète pour X, investit Y, vend pour Z, profit ? »"""
        m = re.search(r'(?:buys?|achète|achète|bought)\s+(?:a|an|the|un|une)?'
                      r'.*?(?:for|pour)\s+(\d+(?:[.,]\d+)?).*?'
                      r'(?:puts? in|investit|repars?|réparations?)\s+'
                      r'(\d+(?:[.,]\d+)?).*?'
                      r'(?:sells?|vend|sold)\s+(?:it|la|le)?.*?(?:for|pour)\s+'
                      r'(\d+(?:[.,]\d+)?)', q)
        if not m:
            return None
        buy, invest, sell = (_num(m.group(1)), _num(m.group(2)),
                             _num(m.group(3)))
        cost = buy + invest
        expr = MathOp('SUB', _lit(sell), _lit(cost))
        return ([f"coût : {_fmt(buy)} + {_fmt(invest)} = {_fmt(cost)}",
                 f"profit : {_fmt(sell)} − {_fmt(cost)} = "
                 f"{_fmt(sell - cost)}"], expr)

    def _solve_remaining(self, q: str) -> Optional[Tuple[List[str], MathOp]]:
        """« X total, Y used/spent, how many left? »
           / « X au total, Y utilisé, combien reste ? »"""
        m = re.search(r'(\d+(?:[.,]\d+)?)\s+(?:total|au total|had|avait).*?'
                      r'(?:used|spent|gave|ate|dépensé|donné|mangé)\s+'
                      r'(\d+(?:[.,]\d+)?).*?(?:left|rest|reste)', q)
        if not m:
            return None
        total, used = _num(m.group(1)), _num(m.group(2))
        expr = MathOp('SUB', _lit(total), _lit(used))
        return ([f"{_fmt(total)} − {_fmt(used)} = {_fmt(total - used)}"],
                expr)

    def _solve_two_purchases(self, q: str) -> Optional[Tuple[List[str], MathOp]]:
        """« X choses à Y € et Z choses à W € » → X×Y + Z×W."""
        m = re.search(r'(\d+)\s+\w+\s+à\s+(\d+(?:[.,]\d+)?)\s*(?:euros?|€)'
                      r'.*?(?:et|plus)\s+(\d+)\s+\w+\s+à\s+'
                      r'(\d+(?:[.,]\d+)?)\s*(?:euros?|€)', q)
        if not m:
            return None
        n1, p1, n2, p2 = (int(m.group(1)), _num(m.group(2)),
                          int(m.group(3)), _num(m.group(4)))
        sub1 = MathOp('MUL', _lit(n1), _lit(p1))
        sub2 = MathOp('MUL', _lit(n2), _lit(p2))
        expr = MathOp('ADD', sub1, sub2)
        steps = [f"{n1} × {_fmt(p1)} = {_fmt(n1 * p1)}",
                 f"{n2} × {_fmt(p2)} = {_fmt(n2 * p2)}",
                 f"{_fmt(n1 * p1)} + {_fmt(n2 * p2)} = "
                 f"{_fmt(n1 * p1 + n2 * p2)}"]
        return steps, expr

    def _solve_speed(self, q: str) -> Optional[Tuple[List[str], MathOp]]:
        """« V km/h pendant T h/min » → V×T. Gère 2h30, 45 min, 3 heures."""
        # Deux formes : "2h30" (compact) ou "3 heures"/"45 minutes"
        m1 = re.search(r'(\d+(?:[.,]\d+)?)\s*km/h.*?(?:pendant|en|durant|pour)\s+'
                       r'(\d+)h\s*(\d+)?', q)
        m2 = re.search(r'(\d+(?:[.,]\d+)?)\s*km/h.*?(?:pendant|en|durant|pour)\s+'
                       r'(\d+(?:[.,]\d+)?)\s*(heures?|min(?:utes)?|h)', q)
        if m1:
            speed, hours = _num(m1.group(1)), float(m1.group(2))
            extra = int(m1.group(3)) if m1.group(3) else 0
            hours += extra / 60.0
            label = f"{m1.group(2)}h{extra or ''}"
        elif m2:
            speed = _num(m2.group(1))
            time_val = _num(m2.group(2))
            unit = m2.group(3)
            hours = time_val / 60.0 if 'min' in unit else time_val
            label = f"{_fmt(time_val)} {'min' if 'min' in unit else 'h'}"
        else:
            return None

        expr = MathOp('MUL', _lit(speed), _lit(hours))
        steps = [f"{label} → {_fmt(hours)} h",
                 f"{_fmt(speed)} × {_fmt(hours)} = {_fmt(speed * hours)} km"]
        return steps, expr

    def _solve_rule_of_three(self, q: str) -> Optional[Tuple[List[str], MathOp]]:
        """« X ouvriers font Y murs en Z jours, combien W ouvriers ? » → Y×W/X."""
        m = re.search(r'(\d+)\s+(?:ouvriers?|personnes?|travailleurs?|maçons?)\s+'
                      r'(?:font|construisent|fabriquent|plantent)\s+(\d+)\s+'
                      r'(?:murs?|maisons?|arbres?|objets?)\s+en\s+(\d+)\s+'
                      r'(?:jours?|heures?).*?(\d+)\s+'
                      r'(?:ouvriers?|personnes?|travailleurs?|maçons?)', q)
        if not m:
            return None
        workers1, output1, days, workers2 = (int(m.group(1)), int(m.group(2)),
                                             int(m.group(3)), int(m.group(4)))
        # Ratio : W2/W1 × output1
        expr = MathOp('MUL', _lit(output1),
                      MathOp('DIV', _lit(workers2), _lit(workers1)))
        ratio = workers2 / workers1
        steps = [f"{workers2} / {workers1} = {_fmt(ratio)} (facteur)",
                 f"{output1} × {_fmt(ratio)} = "
                 f"{_fmt(output1 * ratio)} (mêmes {_fmt(days)} jours)"]
        return steps, expr

    def _solve_nenuphar(self, q: str) -> Optional[Tuple[List[str], MathOp]]:
        """« Nénuphar/bactérie double chaque jour, couvre en N jours, quand la moitié ? »"""
        # Frontières de mots : 'plante' oui, 'plantent' non
        if not re.search(r'\b(?:nénuphar|nenuphar|bactérie|bacterie|plante|'
                         r'algue|fleuri)\b', q):
            return None
        m = re.search(r'(\d+)\s+(?:jours?|j)', q)
        if not m:
            return None
        days = int(m.group(1))
        expr = MathOp('SUB', _lit(days), _lit(1.0))
        return ([f"doublé chaque jour → la moitié est atteinte la veille",
                 f"{days} − 1 = {days - 1} jours"], expr)

    def _solve_handshakes(self, q: str) -> Optional[Tuple[List[str], MathOp]]:
        """« N personnes se serrent la main » → N×(N−1)/2."""
        m = re.search(r'(\d+)\s*(?:personnes?|gens|invités?|amis?)\s+'
                      r'(?:se serrent|serrent|poignées)', q)
        if not m:
            return None
        n = int(m.group(1))
        expr = MathOp('DIV', MathOp('MUL', _lit(n), MathOp('SUB', _lit(n), _lit(1.0))),
                      _lit(2.0))
        return ([f"{n} × ({n} − 1) = {n * (n - 1)} paires ordonnées",
                 f"{n * (n - 1)} / 2 = {n * (n - 1) // 2} poignées"], expr)

    def _solve_seconds(self, q: str) -> Optional[Tuple[List[str], MathOp]]:
        """« combien de minutes/secondes dans X heures/jours »."""
        m = re.search(r'(minutes?|secondes?|heures?|jours?)\s+dans\s+'
                      r'(\d+)\s+(heures?|jours?|minutes?|secondes?)', q)
        if not m:
            return None
        target, n, source = m.group(1), int(m.group(2)), m.group(3)
        # Secondes par unité → facteur = sec(source) / sec(target)
        sec_per = {'seconde': 1, 'secondes': 1, 'minute': 60, 'minutes': 60,
                   'heure': 3600, 'heures': 3600, 'jour': 86400, 'jours': 86400}
        factor = sec_per[source] // sec_per[target]
        expr = MathOp('MUL', _lit(n), _lit(factor))
        return ([f"1 {source.rstrip('s')} = {factor} {target.rstrip('s')}s",
                 f"{n} × {factor} = {n * factor} {target}"], expr)

    def _solve_share(self, q: str) -> Optional[Tuple[List[str], MathOp]]:
        """« X euros partagés entre Y » / "X shared among Y" → X/Y."""
        m = re.search(r'(\d+(?:[.,]\d+)?)\s+\w*\s*(?:partag(?:é|és|ée|ées|er|és)|'
                      r'shared|divided|split)\s+'
                      r'(?:entre|en|par|among|between|by)\s+(\d+)\s*\w*', q)
        if not m:
            return None
        total, parts = _num(m.group(1)), int(m.group(2))
        expr = MathOp('DIV', _lit(total), _lit(parts))
        return ([f"{_fmt(total)} / {parts} = {_fmt(total / parts)} chacun"],
                expr)

    def _solve_increase(self, q: str) -> Optional[Tuple[List[str], MathOp]]:
        """« X augmente de Y% » / "X increased by Y%" → X×(1+Y/100)."""
        m = re.search(r'(\d+(?:[.,]\d+)?)\s+\w+\s+(?:augmente|hausse|'
                      r'increased|rose|rises)\s+(?:de|by)\s+'
                      r'(\d+(?:[.,]\d+)?)\s*%', q)
        if not m:
            return None
        base, pct = _num(m.group(1)), _num(m.group(2))
        expr = MathOp('MUL', _lit(base),
                      MathOp('ADD', _lit(1.0),
                             MathOp('DIV', _lit(pct), _lit(100.0))))
        return ([f"1 + {_fmt(pct)}/100 = {_fmt(1 + pct / 100)}",
                 f"{_fmt(base)} × {_fmt(1 + pct / 100)} = "
                 f"{_fmt(base * (1 + pct / 100))}"], expr)

    def _solve_discount(self, q: str) -> Optional[Tuple[List[str], MathOp]]:
        """« X € avec Y% de réduction » / "X with Y% off" → X×(1−Y/100)."""
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:€|euros?|dollars?|\$)?'
                      r'\s*(?:avec|à|with)\s+'
                      r'(\d+(?:[.,]\d+)?)\s*%\s*(?:de\s+)?'
                      r'(?:réduction|remise|solde|off|discount)', q)
        if not m:
            return None
        price, pct = _num(m.group(1)), _num(m.group(2))
        expr = MathOp('MUL', _lit(price),
                      MathOp('SUB', _lit(1.0),
                             MathOp('DIV', _lit(pct), _lit(100.0))))
        return ([f"1 − {_fmt(pct)}/100 = {_fmt(1 - pct / 100)}",
                 f"{_fmt(price)} × {_fmt(1 - pct / 100)} = "
                 f"{_fmt(price * (1 - pct / 100))}"], expr)

    def solve_and_emit(self, question: str) -> Optional[Tuple[WordProblemResult, str]]:
        """Résout et retourne (résultat, code Python converti)."""
        r = self.solve(question)
        if r is None:
            return None
        py = emit_python(Program([Assign("resultat", self._parse_expr(r.expression)),
                                  Return(Var("resultat"))]),
                         include_wave_lang=False, include_holograms=False)
        return r, py

    def _parse_expr(self, expression: str):
        """Re-parse une expression harmonique (pour l'émission)."""
        from wave_ir import parse
        prog = parse(expression)
        for stmt in prog.statements:
            if isinstance(stmt, Assign):
                return stmt.value
        return Literal(0.0)


# ═══════════════════════════════════════════════════════════════════════════════
# BENCHMARK — 30 problèmes multi-étapes
# ═══════════════════════════════════════════════════════════════════════════════

# (question, réponse attendue, méthode)
WORD_PROBLEMS: List[Tuple[str, float, str]] = [
    # Vitesse
    ("Un train roule à 100 km/h pendant 2h30. Quelle distance parcourt-il ?", 250.0, "vitesse"),
    ("Un train roule à 100 km/h pendant 2h30. Quelle distance parcourt-il ?", 250.0, "vitesse"),
    ("Une voiture roule à 80 km/h pendant 3 heures. Quelle distance ?", 240.0, "vitesse"),
    ("Un cycliste roule à 20 km/h pendant 45 minutes. Quelle distance ?", 15.0, "vitesse"),
    ("Un avion vole à 900 km/h pendant 4 heures. Quelle distance ?", 3600.0, "vitesse"),
    # Achats
    ("Marie achète 3 pommes à 2 euros chacune. Combien paie-t-elle ?", 6.0, "achat"),
    ("Pierre achète 5 livres à 8 euros chacun. Combien paie-t-il ?", 40.0, "achat"),
    ("Un client achète 4 baguettes à 1 euro chacune. Combien paie-t-il ?", 4.0, "achat"),
    ("Paul achète 2 cahiers à 3 euros et 3 stylos à 2 euros. Combien paie-t-il ?", 12.0, "achats combinés"),
    ("Sarah achète 3 places à 10 euros et 2 places à 5 euros. Combien paie-t-elle ?", 40.0, "achats combinés"),
    # Règle de trois
    ("Si 3 ouvriers construisent 3 murs en 3 jours, combien de murs 6 ouvriers construisent-ils en 3 jours ?", 6.0, "règle de trois"),
    ("Si 2 maçons construisent 2 maisons en 4 jours, combien de maisons 4 maçons construisent-ils ?", 4.0, "règle de trois"),
    ("Si 5 personnes plantent 10 arbres en 1 jour, combien d'arbres 10 personnes plantent-elles ?", 20.0, "règle de trois"),
    # Nénuphar
    ("Un nénuphar double sa surface chaque jour. Il couvre l'étang en 48 jours. Quand couvre-t-il la moitié ?", 47.0, "nénuphar"),
    ("Une bactérie double chaque jour. Elle remplit le flacon en 30 jours. Quand remplit-elle la moitié ?", 29.0, "nénuphar"),
    # Poignées de main
    ("10 personnes se serrent la main. Combien de poignées de main ?", 45.0, "poignées de main"),
    ("6 amis se serrent la main. Combien de poignées de main ?", 15.0, "poignées de main"),
    # Secondes
    ("Combien de secondes dans 2 heures ?", 7200.0, "secondes"),
    ("Combien de secondes dans 1 jour ?", 86400.0, "secondes"),
    # Partage
    ("120 euros partagés entre 4 personnes. Combien chacun ?", 30.0, "partage"),
    ("100 bonbons partagés entre 5 enfants. Combien chacun ?", 20.0, "partage"),
    # Augmentation / réduction
    ("Un prix de 50 euros augmente de 10%. Quel est le nouveau prix ?", 55.0, "augmentation"),
    ("Un prix de 80 euros avec 25% de réduction. Quel est le prix final ?", 60.0, "réduction"),
    ("Un salaire de 2000 euros augmente de 5%. Quel est le nouveau salaire ?", 2100.0, "augmentation"),
    ("Un manteau de 120 euros avec 50% de solde. Quel est le prix final ?", 60.0, "réduction"),
    # Enchaînés (via le parseur math direct)
    ("Calcule 2 plus 3 fois 4", 14.0, "enchaîné"),
    ("Calcule 10 plus 5 fois 2", 20.0, "enchaîné"),
    ("Calcule 100 divisé par 4 plus 5", 30.0, "enchaîné"),
    # Divers
    ("Combien de minutes dans 3 heures ?", 180.0, "secondes"),
    ("48 pommes partagées entre 6 paniers. Combien par panier ?", 8.0, "partage"),
]


def run_benchmark_word_problems(verbose: bool = True) -> Dict:
    """Exécute le benchmark des problèmes multi-étapes."""
    engine = WaveWordProblemEngine()
    passed, total = 0, 0

    for question, expected, method in WORD_PROBLEMS:
        r = engine.solve(question)
        if r is None:
            ok = False
        else:
            ok = abs(r.result - expected) < 1e-6
        passed += ok
        total += 1
        if verbose:
            mark = '✅' if ok else '❌'
            got = r.result if r else "AUCUN PATTERN"
            print(f"  {mark} [{method:<16}] {question[:52]:<54} → {got} (attendu: {expected})")

    return {
        'passed': passed,
        'total': total,
        'score': 100.0 * passed / total,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 65)
    print("  🌊 WAVE WORD PROBLEMS — Moteur multi-étapes")
    print("=" * 65)
    print()

    # Démonstration détaillée
    engine = WaveWordProblemEngine()
    for q in ["Un train roule à 100 km/h pendant 2h30. Quelle distance parcourt-il ?",
              "Si 3 ouvriers construisent 3 murs en 3 jours, combien de murs 6 ouvriers ?",
              "Un nénuphar double chaque jour, il couvre l'étang en 48 jours, quand la moitié ?",
              "10 personnes se serrent la main. Combien de poignées ?"]:
        r = engine.solve(q)
        if r:
            print(f"❓ {q}")
            print(f"   Expression : {r.expression}")
            for s in r.steps:
                print(f"   · {s}")
            print()

    # Benchmark
    print("── BENCHMARK (30 problèmes) ──")
    stats = run_benchmark_word_problems(verbose=True)
    print(f"\n  📊 SCORE : {stats['passed']}/{stats['total']} ({stats['score']:.1f}%)")
    print("=" * 65)
